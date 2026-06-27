from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.language import detect_language
from app.models.agent import AgentConfig, GraphRunStatus
from app.models.evaluation import (
    EvaluationCase,
    EvaluationMetric,
    EvaluationMode,
    EvaluationResult,
    EvaluationRun,
    EvaluationRunStatus,
)
from app.models.user import User
from app.services.agent_service import AgentService
from app.services.evaluation_loader import LoadedEvaluationCase, load_jsonl_cases
from app.services.evaluation_metrics import calculate_metrics
from app.services.model_provider import MockModelProvider
from app.services.retrieval_service import RetrievalService
from app.services.token_accounting import estimate_tokens


class EvaluationRunNotFoundError(ValueError):
    pass


class EvaluationRunner:
    def __init__(self, db: Session):
        self.db = db

    def run_from_jsonl(
        self,
        *,
        workspace_id: UUID,
        name: str,
        jsonl_cases: str,
        modes: list[EvaluationMode],
        current_user: User,
        agent_id: UUID | None,
    ) -> EvaluationRun:
        loaded_cases = load_jsonl_cases(jsonl_cases)
        run = EvaluationRun(
            workspace_id=workspace_id,
            name=name.strip(),
            modes_json=json.dumps([mode.value for mode in modes]),
            status=EvaluationRunStatus.running,
            total_cases=len(loaded_cases),
            created_by_user_id=current_user.id,
        )
        self.db.add(run)
        self.db.flush()
        cases = [self._persist_case(workspace_id, loaded_case) for loaded_case in loaded_cases]
        self.db.commit()
        if EvaluationMode.system_v1 in modes:
            agent_id = agent_id or self._ensure_default_agent(workspace_id).id
        results: list[EvaluationResult] = []
        for case, loaded_case in zip(cases, loaded_cases, strict=True):
            for mode in modes:
                result = self._run_case(
                    workspace_id=workspace_id,
                    run_id=run.id,
                    case=case,
                    loaded_case=loaded_case,
                    mode=mode,
                    current_user=current_user,
                    agent_id=agent_id,
                )
                results.append(result)
        for (mode, language), metric_values in calculate_metrics(results).items():
            for metric_name, metric_value in metric_values.items():
                self.db.add(
                    EvaluationMetric(
                        workspace_id=workspace_id,
                        evaluation_run_id=run.id,
                        mode=EvaluationMode(mode),
                        language=language,
                        metric_name=metric_name,
                        metric_value=metric_value,
                    )
                )
        run.status = EvaluationRunStatus.completed
        run.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_runs(self, *, workspace_id: UUID) -> list[EvaluationRun]:
        return list(
            self.db.scalars(
                select(EvaluationRun)
                .where(EvaluationRun.workspace_id == workspace_id)
                .order_by(EvaluationRun.created_at.desc())
            ).all()
        )

    def get_run_detail(self, *, workspace_id: UUID, run_id: UUID) -> EvaluationRun:
        run = self.db.scalar(
            select(EvaluationRun)
            .options(selectinload(EvaluationRun.results), selectinload(EvaluationRun.metrics))
            .where(EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id)
        )
        if run is None:
            raise EvaluationRunNotFoundError("Evaluation run was not found.")
        run.results.sort(key=lambda result: result.created_at)
        run.metrics.sort(
            key=lambda metric: (str(metric.mode), str(metric.language), metric.metric_name)
        )
        return run

    def _persist_case(
        self, workspace_id: UUID, loaded_case: LoadedEvaluationCase
    ) -> EvaluationCase:
        case = EvaluationCase(
            workspace_id=workspace_id,
            external_id=loaded_case.external_id,
            language=loaded_case.language,
            input_message=loaded_case.input_message,
            expected_intent=loaded_case.expected_intent,
            expected_sources_json=json.dumps(loaded_case.expected_sources, ensure_ascii=False),
            must_include_json=json.dumps(loaded_case.must_include, ensure_ascii=False),
            must_not_include_json=json.dumps(loaded_case.must_not_include, ensure_ascii=False),
            expected_route=loaded_case.expected_route,
            safety_risk=loaded_case.safety_risk,
            max_prompt_tokens=loaded_case.max_prompt_tokens,
            metadata_json=json.dumps(loaded_case.metadata, ensure_ascii=False),
        )
        self.db.add(case)
        self.db.flush()
        return case

    def _ensure_default_agent(self, workspace_id: UUID) -> AgentConfig:
        agent = self.db.scalar(
            select(AgentConfig).where(AgentConfig.workspace_id == workspace_id).limit(1)
        )
        if agent is not None:
            return agent
        return AgentService(self.db).create_agent(
            workspace_id=workspace_id, name="Evaluation Agent", token_budget=4000
        )

    def _run_case(
        self,
        *,
        workspace_id: UUID,
        run_id: UUID,
        case: EvaluationCase,
        loaded_case: LoadedEvaluationCase,
        mode: EvaluationMode,
        current_user: User,
        agent_id: UUID | None,
    ) -> EvaluationResult:
        started = time.perf_counter()
        answer: str | None = None
        citations: list[str] = []
        actual_route = "finalize"
        prompt_tokens = estimate_tokens(loaded_case.input_message, loaded_case.language)
        estimated_cost = 0.0
        error_message = None
        try:
            if mode == EvaluationMode.direct_llm:
                response = MockModelProvider(self.db).complete(
                    workspace_id=workspace_id,
                    purpose="evaluation_direct_llm",
                    language=loaded_case.language,
                    prompt=loaded_case.input_message,
                    model="mock-standard",
                    completion_text=_direct_answer(loaded_case.language),
                )
                answer = response.content
                prompt_tokens = response.ai_run.prompt_tokens
                estimated_cost = response.ai_run.estimated_cost
            elif mode == EvaluationMode.vector_rag:
                retrieval = RetrievalService(self.db).search(
                    workspace_id=workspace_id,
                    query=loaded_case.input_message,
                    language=loaded_case.language,
                    top_k=4,
                    min_score=0.2,
                    document_id=None,
                )
                citations = [result.citation for result in retrieval.results]
                actual_route = "human_review" if retrieval.no_source else "finalize"
                answer = _rag_answer(loaded_case.language) if not retrieval.no_source else None
            else:
                graph_run = AgentService(self.db).run_agent(
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    input_message=loaded_case.input_message,
                    current_user=current_user,
                )
                actual_route = (
                    "finalize" if graph_run.status == GraphRunStatus.completed else "human_review"
                )
                answer = graph_run.final_answer
                trace = AgentService(self.db).get_trace(
                    workspace_id=workspace_id, run_id=graph_run.id
                )
                citations = _citations_from_steps(trace)
                prompt_tokens = sum(step.token_count or 0 for step in trace.steps) or prompt_tokens
                estimated_cost = sum(step.estimated_cost or 0.0 for step in trace.steps)
        except Exception as exc:
            actual_route = "error"
            error_message = str(exc)
        latency_ms = max(1, int((time.perf_counter() - started) * 1000))
        scores = _score_case(
            loaded_case=loaded_case,
            actual_route=actual_route,
            answer=answer,
            citations=citations,
        )
        result = EvaluationResult(
            workspace_id=workspace_id,
            evaluation_run_id=run_id,
            evaluation_case_id=case.id,
            mode=mode,
            language=loaded_case.language,
            actual_route=actual_route,
            answer=answer,
            citations_json=json.dumps(citations, ensure_ascii=False),
            passed=all(value >= 1.0 for value in scores.values() if isinstance(value, int | float)),
            scores_json=json.dumps(scores, ensure_ascii=False, sort_keys=True),
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            estimated_cost=estimated_cost,
            error_message=error_message,
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result


def _score_case(
    *,
    loaded_case: LoadedEvaluationCase,
    actual_route: str,
    answer: str | None,
    citations: list[str],
) -> dict[str, float]:
    answer_text = answer or ""
    route_match = 1.0 if actual_route == loaded_case.expected_route else 0.0
    must_include = 1.0 if all(item in answer_text for item in loaded_case.must_include) else 0.0
    must_not_include = (
        1.0 if all(item not in answer_text for item in loaded_case.must_not_include) else 0.0
    )
    citation_accuracy = 1.0
    if loaded_case.expected_sources:
        citation_accuracy = 1.0 if any(
            expected in citation
            for expected in loaded_case.expected_sources
            for citation in citations
        ) else 0.0
    elif loaded_case.expected_route == "finalize":
        citation_accuracy = 1.0 if citations else 0.0
    groundedness = 1.0 if loaded_case.expected_route != "finalize" or bool(citations) else 0.0
    language_preserved = _language_preserved(answer_text, loaded_case.language)
    return {
        "route_match": route_match,
        "must_include": must_include,
        "must_not_include": must_not_include,
        "citation_accuracy": citation_accuracy,
        "groundedness": groundedness,
        "language_preserved": language_preserved,
    }


def _language_preserved(answer: str, language) -> float:
    if not answer:
        return 1.0
    try:
        return 1.0 if detect_language(answer) == language else 0.0
    except ValueError:
        return 0.0


def _citations_from_steps(graph_run) -> list[str]:
    for step in graph_run.steps:
        if step.step_name == "retrieve_evidence":
            try:
                output = json.loads(step.output_json)
            except json.JSONDecodeError:
                return []
            return list(output.get("citations", []))
    return []


def _direct_answer(language) -> str:
    if str(language) == "ja":
        return "返金についてはサポートに確認してください。"
    if str(language) == "zh":
        return "请联系支持团队确认退款政策。"
    return "Please contact support to confirm the refund policy."


def _rag_answer(language) -> str:
    if str(language) == "ja":
        return "関連資料によると、返金は30日以内に申請できます。"
    if str(language) == "zh":
        return "根据相关资料，退款可以在30天内申请。"
    return "According to the retrieved policy, refunds can be requested within 30 days."
