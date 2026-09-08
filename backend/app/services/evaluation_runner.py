from __future__ import annotations

import json
import time
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.agent import AgentConfig, GraphRunStatus
from app.models.evaluation import (
    EvaluationCase,
    EvaluationMode,
    EvaluationResult,
    EvaluationRun,
    EvaluationRunStatus,
)
from app.models.review import GuardrailResult
from app.models.user import User
from app.services.agent_service import AgentNotFoundError, AgentService
from app.services.evaluation_comparison import compare_metrics
from app.services.evaluation_direct_baseline import run_direct_baseline
from app.services.evaluation_execution import evaluation_execution
from app.services.evaluation_loader import LoadedEvaluationCase, load_jsonl_cases
from app.services.evaluation_management import (
    EvaluationManagement,
)
from app.services.evaluation_management import (
    EvaluationRunNotArchivedError as EvaluationRunNotArchivedError,
)
from app.services.evaluation_management import (
    EvaluationRunNotFoundError as EvaluationRunNotFoundError,
)
from app.services.evaluation_rag_baseline import run_rag_baseline
from app.services.evaluation_scoring import _score_case as _score_case
from app.services.evaluation_usage import graph_model_usage
from app.services.folder_service import ResourceFolderService
from app.services.model_provider import ModelProviderError


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
        with evaluation_execution(self.db, run) as results:
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

    def move_run(self, *, workspace_id: UUID, run_id: UUID, folder_id: UUID | None,
                 actor_user_id: UUID) -> EvaluationRun:
        return EvaluationManagement(self.db).move_run(
            workspace_id=workspace_id, run_id=run_id, folder_id=folder_id,
            actor_user_id=actor_user_id)

    def archive_run(self, *, workspace_id: UUID, run_id: UUID,
                    actor_user_id: UUID) -> EvaluationRun:
        return EvaluationManagement(self.db).archive_run(
            workspace_id=workspace_id, run_id=run_id, actor_user_id=actor_user_id)

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
        deltas = compare_metrics(current_run, baseline_run)
        return current_run, baseline_run, deltas

    def delete_archived_run(self, *, workspace_id: UUID, run_id: UUID,
                            actor_user_id: UUID) -> EvaluationRun:
        return EvaluationManagement(self.db).delete_archived_run(
            workspace_id=workspace_id, run_id=run_id, actor_user_id=actor_user_id)

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
        prompt_tokens = 0
        estimated_cost = 0.0
        error_message = None
        actual_tool_calls: list[str] = []
        actual_guardrail_failures: list[str] = []
        graph_run_id: UUID | None = None
        try:
            if mode == EvaluationMode.direct_llm:
                response = run_direct_baseline(self.db, workspace_id=workspace_id,
                    evaluation_run_id=run_id, question=loaded_case.input_message,
                    language=loaded_case.language)
                answer = response.content
                prompt_tokens = response.ai_run.prompt_tokens
                estimated_cost = response.ai_run.estimated_cost
            elif mode == EvaluationMode.vector_rag:
                rag = run_rag_baseline(self.db, workspace_id=workspace_id,
                                       question=loaded_case.input_message,
                                       language=loaded_case.language, evaluation_run_id=run_id)
                answer, citations, actual_route = rag.answer, rag.citations, rag.route
                prompt_tokens, estimated_cost = rag.prompt_tokens, rag.estimated_cost
            else:
                graph_run = AgentService(self.db).run_agent(
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    input_message=loaded_case.input_message,
                    current_user=current_user, language=loaded_case.language,
                )
                graph_run_id = graph_run.id
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
                prompt_tokens, estimated_cost = graph_model_usage(self.db, workspace_id, trace.id)
        except Exception as exc:
            actual_route = "error"
            error_message = str(exc)
            if isinstance(exc, ModelProviderError) and exc.ai_run is not None:
                prompt_tokens = exc.ai_run.prompt_tokens
                estimated_cost = exc.ai_run.estimated_cost
        latency_ms = max(1, int((time.perf_counter() - started) * 1000))
        scores = _score_case(
            loaded_case=loaded_case, prompt_tokens=prompt_tokens,
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
            graph_run_id=graph_run_id,
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
