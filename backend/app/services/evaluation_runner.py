from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
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
from app.models.review import GuardrailResult
from app.models.user import User
from app.services.agent_service import AgentNotFoundError, AgentService
from app.services.evaluation_loader import LoadedEvaluationCase, load_jsonl_cases
from app.services.evaluation_metrics import calculate_metrics
from app.services.folder_service import ResourceFolderService
from app.services.model_provider import MockModelProvider
from app.services.retrieval_service import RetrievalService
from app.services.token_accounting import estimate_tokens


class EvaluationRunNotFoundError(ValueError):
    pass


class EvaluationRunNotArchivedError(ValueError):
    pass


LOWER_IS_BETTER_METRICS = {
    "average_latency_ms",
    "average_prompt_tokens",
    "estimated_cost_per_run",
}
METRIC_DELTA_TOLERANCE = 0.000001


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
        folder_id: UUID | None = None,
    ) -> EvaluationRun:
        loaded_cases = load_jsonl_cases(jsonl_cases)
        ResourceFolderService(self.db).validate_folder(
            workspace_id=workspace_id, folder_id=folder_id, resource_type="evaluation_run"
        )
        attached_agent_id = agent_id
        if EvaluationMode.system_v1 in modes and attached_agent_id is None:
            attached_agent_id = self._ensure_default_agent(workspace_id).id
        if (
            attached_agent_id is not None
            and AgentService(self.db).get_agent(
                workspace_id=workspace_id, agent_id=attached_agent_id
            )
            is None
        ):
            raise AgentNotFoundError("Agent was not found.")
        run = EvaluationRun(
            workspace_id=workspace_id,
            name=name.strip(),
            folder_id=folder_id,
            agent_config_id=attached_agent_id,
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
            agent_id = attached_agent_id
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

    def list_runs(
        self,
        *,
        workspace_id: UUID,
        include_archived: bool = False,
        archived_only: bool = False,
        folder_id: UUID | None = None,
        unfiled: bool = False,
        search: str | None = None,
        status_filter: EvaluationRunStatus | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[EvaluationRun]:
        ResourceFolderService(self.db).validate_folder(
            workspace_id=workspace_id, folder_id=folder_id, resource_type="evaluation_run"
        )
        filters = [EvaluationRun.workspace_id == workspace_id]
        if folder_id is not None:
            filters.append(EvaluationRun.folder_id == folder_id)
        elif unfiled:
            filters.append(EvaluationRun.folder_id.is_(None))
        if archived_only:
            filters.append(EvaluationRun.archived_at.is_not(None))
        elif not include_archived:
            filters.append(EvaluationRun.archived_at.is_(None))
        if status_filter is not None:
            filters.append(EvaluationRun.status == status_filter)
        normalized_search = (search or "").strip()
        if normalized_search:
            pattern = f"%{normalized_search}%"
            filters.append(
                or_(
                    EvaluationRun.name.ilike(pattern),
                    EvaluationRun.modes_json.ilike(pattern),
                    EvaluationRun.status.ilike(pattern),
                )
            )
        statement = (
            select(EvaluationRun)
            .where(*filters)
            .order_by(EvaluationRun.created_at.desc())
            .offset(offset)
        )
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.db.scalars(statement).all())

    def move_run(
        self, *, workspace_id: UUID, run_id: UUID, folder_id: UUID | None
    ) -> EvaluationRun:
        ResourceFolderService(self.db).validate_folder(
            workspace_id=workspace_id, folder_id=folder_id, resource_type="evaluation_run"
        )
        run = self.db.scalar(
            select(EvaluationRun).where(
                EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id
            )
        )
        if run is None:
            raise EvaluationRunNotFoundError("Evaluation run was not found.")
        run.folder_id = folder_id
        self.db.commit()
        self.db.refresh(run)
        return run

    def archive_run(self, *, workspace_id: UUID, run_id: UUID) -> EvaluationRun:
        run = self.db.scalar(
            select(EvaluationRun).where(
                EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id
            )
        )
        if run is None:
            raise EvaluationRunNotFoundError("Evaluation run was not found.")
        if run.archived_at is None:
            run.archived_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(run)
        return run

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

    def compare_runs(
        self, *, workspace_id: UUID, current_run_id: UUID, baseline_run_id: UUID
    ) -> tuple[EvaluationRun, EvaluationRun, list[dict[str, object]]]:
        current_run = self.get_run_detail(workspace_id=workspace_id, run_id=current_run_id)
        baseline_run = self.get_run_detail(workspace_id=workspace_id, run_id=baseline_run_id)
        current_metrics = {
            (str(metric.mode), str(metric.language), metric.metric_name): metric.metric_value
            for metric in current_run.metrics
        }
        baseline_metrics = {
            (str(metric.mode), str(metric.language), metric.metric_name): metric.metric_value
            for metric in baseline_run.metrics
        }
        keys = sorted(
            set(current_metrics) | set(baseline_metrics),
            key=lambda item: (item[0], item[1], _metric_sort_key(item[2])),
        )
        deltas: list[dict[str, object]] = []
        for mode, language, metric_name in keys:
            current_value = current_metrics.get((mode, language, metric_name))
            baseline_value = baseline_metrics.get((mode, language, metric_name))
            delta = (
                current_value - baseline_value
                if current_value is not None and baseline_value is not None
                else None
            )
            deltas.append(
                {
                    "mode": mode,
                    "language": language,
                    "metric_name": metric_name,
                    "current_value": current_value,
                    "baseline_value": baseline_value,
                    "delta": delta,
                    "direction": _metric_direction(metric_name, current_value, baseline_value),
                }
            )
        return current_run, baseline_run, deltas

    def delete_archived_run(self, *, workspace_id: UUID, run_id: UUID) -> EvaluationRun:
        run = self.db.scalar(
            select(EvaluationRun)
            .options(selectinload(EvaluationRun.results), selectinload(EvaluationRun.metrics))
            .where(EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id)
        )
        if run is None:
            raise EvaluationRunNotFoundError("Evaluation run was not found.")
        if run.archived_at is None:
            raise EvaluationRunNotArchivedError(
                "Archive the evaluation run before permanent deletion."
            )

        case_ids = [result.evaluation_case_id for result in run.results]
        for metric in list(run.metrics):
            self.db.delete(metric)
        for result in list(run.results):
            self.db.delete(result)
        for case_id in case_ids:
            case = self.db.scalar(
                select(EvaluationCase).where(
                    EvaluationCase.workspace_id == workspace_id,
                    EvaluationCase.id == case_id,
                )
            )
            if case is not None:
                self.db.delete(case)
        self.db.delete(run)
        self.db.commit()
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
            metadata_json=json.dumps(
                {
                    **loaded_case.metadata,
                    "expected_tool_calls": loaded_case.expected_tool_calls,
                    "expected_guardrail_failures": loaded_case.expected_guardrail_failures,
                },
                ensure_ascii=False,
            ),
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
        actual_tool_calls: list[str] = []
        actual_guardrail_failures: list[str] = []
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
                actual_tool_calls = _tool_calls_from_steps(trace)
                actual_guardrail_failures = _failed_guardrails_for_run(
                    self.db, workspace_id=workspace_id, run_id=graph_run.id
                )
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
            actual_tool_calls=actual_tool_calls,
            actual_guardrail_failures=actual_guardrail_failures,
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
    actual_tool_calls: list[str],
    actual_guardrail_failures: list[str],
) -> dict[str, float | list[str]]:
    answer_text = answer or ""
    route_match = 1.0 if actual_route == loaded_case.expected_route else 0.0
    must_include = 1.0 if all(item in answer_text for item in loaded_case.must_include) else 0.0
    must_not_include = (
        1.0 if all(item not in answer_text for item in loaded_case.must_not_include) else 0.0
    )
    citation_accuracy = 1.0
    if loaded_case.expected_sources:
        citation_accuracy = (
            1.0
            if any(
                expected in citation
                for expected in loaded_case.expected_sources
                for citation in citations
            )
            else 0.0
        )
    elif loaded_case.expected_route == "finalize":
        citation_accuracy = 1.0 if citations else 0.0
    groundedness = 1.0 if loaded_case.expected_route != "finalize" or bool(citations) else 0.0
    language_preserved = _language_preserved(answer_text, loaded_case.language)
    tool_call_match = _expected_subset_score(loaded_case.expected_tool_calls, actual_tool_calls)
    guardrail_failure_match = _expected_subset_score(
        loaded_case.expected_guardrail_failures, actual_guardrail_failures
    )
    return {
        "route_match": route_match,
        "must_include": must_include,
        "must_not_include": must_not_include,
        "citation_accuracy": citation_accuracy,
        "groundedness": groundedness,
        "language_preserved": language_preserved,
        "tool_call_match": tool_call_match,
        "guardrail_failure_match": guardrail_failure_match,
        "actual_tool_calls": actual_tool_calls,
        "actual_guardrail_failures": actual_guardrail_failures,
    }


def _expected_subset_score(expected: list[str], actual: list[str]) -> float:
    if not expected:
        return 1.0
    actual_set = set(actual)
    return 1.0 if all(item in actual_set for item in expected) else 0.0


def _language_preserved(answer: str, language) -> float:
    if not answer:
        return 1.0
    try:
        return 1.0 if detect_language(answer) == language else 0.0
    except ValueError:
        return 0.0


def _failed_guardrails_for_run(db: Session, *, workspace_id: UUID, run_id: UUID) -> list[str]:
    return list(
        db.scalars(
            select(GuardrailResult.guardrail_type)
            .where(
                GuardrailResult.workspace_id == workspace_id,
                GuardrailResult.graph_run_id == run_id,
                GuardrailResult.passed.is_(False),
            )
            .order_by(GuardrailResult.created_at.asc())
        ).all()
    )


def _tool_calls_from_steps(graph_run) -> list[str]:
    names: list[str] = []
    for step in graph_run.steps:
        names.extend(tool_call.tool_name for tool_call in step.tool_calls)
    return names


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


def _metric_sort_key(metric_name: str) -> tuple[int, str]:
    order = [
        "case_pass_rate",
        "human_review_routing_accuracy",
        "tool_call_correctness",
        "guardrail_failure_detection_rate",
        "groundedness_pass_rate",
        "citation_accuracy",
        "language_preservation_pass_rate",
        "average_prompt_tokens",
        "estimated_cost_per_run",
        "average_latency_ms",
    ]
    try:
        return order.index(metric_name), metric_name
    except ValueError:
        return len(order), metric_name


def _metric_direction(
    metric_name: str, current_value: float | None, baseline_value: float | None
) -> str:
    if current_value is None:
        return "missing"
    if baseline_value is None:
        return "new"
    delta = current_value - baseline_value
    if abs(delta) <= METRIC_DELTA_TOLERANCE:
        return "unchanged"
    if metric_name in LOWER_IS_BETTER_METRICS:
        return "improved" if delta < 0 else "regressed"
    return "improved" if delta > 0 else "regressed"
