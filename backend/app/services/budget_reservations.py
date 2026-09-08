"""Admission transactions serialize by workspace; no provider I/O occurs under this lock."""

from datetime import UTC, datetime, timedelta
from math import isfinite
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig, GraphRun
from app.models.ai import AIRun
from app.models.budget import WorkspaceBudgetPolicy
from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.reservation import ModelCallReservation
from app.models.workspace import Workspace
from app.services.token_budget import ModelCallBudgetPlan


class BudgetReservationDenied(ValueError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class EvaluationReservationActive(ValueError):
    pass


class BudgetReservationService:
    def __init__(self, db: Session):
        self.db = db

    def reserve(self, *, workspace_id: UUID, graph_run_id: UUID | None = None, purpose: str,
                plan: ModelCallBudgetPlan, evaluation_run_id: UUID | None = None,
                lifetime_seconds: int = 300) -> ModelCallReservation:
        if (graph_run_id is None) == (evaluation_run_id is None):
            raise ValueError("Exactly one graph or evaluation context is required")
        if (plan.total_tokens < 0 or not isfinite(plan.estimated_cost)
                or plan.estimated_cost < 0 or lifetime_seconds <= 0):
            raise ValueError("Invalid reservation estimate or lifetime")
        now = datetime.now(UTC)
        # Workspace always exists even before a policy is created, avoiding missing-row lock races.
        workspace = self.db.scalar(select(Workspace).where(
            Workspace.id == workspace_id).with_for_update())
        run = self.db.scalar(select(GraphRun).where(
            GraphRun.workspace_id == workspace_id, GraphRun.id == graph_run_id))
        evaluation = self.db.scalar(select(EvaluationRun).where(
            EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == evaluation_run_id,
            EvaluationRun.status == EvaluationRunStatus.running,
            EvaluationRun.archived_at.is_(None))) if evaluation_run_id else None
        if workspace is None or (run is None and evaluation is None):
            self.db.rollback()
            raise ValueError("Workspace graph or active evaluation run was not found")
        agent = self.db.scalar(select(AgentConfig).where(
            AgentConfig.workspace_id == workspace_id,
            AgentConfig.id == run.agent_config_id)) if run else None
        if run is not None and agent is None:
            self.db.rollback()
            raise ValueError("Workspace agent was not found")
        policy = self.db.scalar(select(WorkspaceBudgetPolicy).where(
            WorkspaceBudgetPolicy.workspace_id == workspace_id
        ).execution_options(populate_existing=True))
        if policy is None:
            policy = WorkspaceBudgetPolicy(workspace_id=workspace_id)
            self.db.add(policy)
            self.db.flush()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = self.usage(workspace_id, now, since=month_start)
        current = self.usage(workspace_id, now, graph_run_id=graph_run_id,
                             evaluation_run_id=evaluation_run_id)
        token_limit = policy.per_run_token_budget
        if agent:
            token_limit = min(agent.token_budget, token_limit)
        reason = None
        if not plan.allowed:
            reason = "model_context_exceeded"
        elif current[0] + plan.total_tokens > token_limit:
            reason = "token_budget_exceeded"
        elif current[1] + plan.estimated_cost > policy.per_run_cost_budget:
            reason = "cost_budget_exceeded"
        elif monthly[0] + plan.total_tokens > policy.monthly_token_budget:
            reason = "monthly_token_budget_exceeded"
        elif monthly[1] + plan.estimated_cost > policy.monthly_cost_budget:
            reason = "monthly_cost_budget_exceeded"
        reservation = ModelCallReservation(
            workspace_id=workspace_id, graph_run_id=graph_run_id, purpose=purpose,
            evaluation_run_id=evaluation_run_id,
            estimated_tokens=plan.total_tokens, estimated_cost=plan.estimated_cost,
            status="denied" if reason else "reserved", denial_reason=reason,
            created_at=now, expires_at=now + timedelta(seconds=lifetime_seconds),
            finalized_at=now if reason else None,
        )
        self.db.add(reservation)
        self.db.commit()
        if reason:
            raise BudgetReservationDenied(reason)
        self.db.refresh(reservation)
        return reservation

    def usage(self, workspace_id, now, *, since=None, graph_run_id=None, evaluation_run_id=None):
        ledger_filters = [AIRun.workspace_id == workspace_id]
        # Age is not evidence that a dispatched provider call ended or was unbilled.
        active_filters = [ModelCallReservation.workspace_id == workspace_id,
                          ModelCallReservation.status == "reserved"]
        if since is not None:
            ledger_filters.append(AIRun.created_at >= since)
        if graph_run_id is not None:
            ledger_filters.append(AIRun.graph_run_id == graph_run_id)
            active_filters.append(ModelCallReservation.graph_run_id == graph_run_id)
        if evaluation_run_id is not None:
            ledger_filters.append(AIRun.id.in_(select(ModelCallReservation.ai_run_id).where(
                ModelCallReservation.workspace_id == workspace_id,
                ModelCallReservation.evaluation_run_id == evaluation_run_id)))
            active_filters.append(ModelCallReservation.evaluation_run_id == evaluation_run_id)
        ledger = self.db.execute(select(func.coalesce(func.sum(AIRun.total_tokens), 0),
            func.coalesce(func.sum(AIRun.estimated_cost), 0)).where(*ledger_filters)).one()
        active = self.db.execute(select(
            func.coalesce(func.sum(ModelCallReservation.estimated_tokens), 0),
            func.coalesce(func.sum(ModelCallReservation.estimated_cost), 0)
        ).where(*active_filters)).one()
        return int(ledger[0] + active[0]), float(ledger[1] + active[1])

    def guard_evaluation_delete(self, workspace_id: UUID, evaluation_run_id: UUID) -> None:
        self.db.scalar(select(Workspace).where(Workspace.id == workspace_id).with_for_update())
        active = self.db.scalar(select(ModelCallReservation.id).where(
            ModelCallReservation.workspace_id == workspace_id,
            ModelCallReservation.evaluation_run_id == evaluation_run_id,
            ModelCallReservation.status == "reserved").limit(1))
        if active is not None:
            raise EvaluationReservationActive("Evaluation has active model-call reservations.")

    def finalize(self, *, workspace_id: UUID, reservation_id: UUID,
                 ai_run_id: UUID | None = None, uncertain: bool = False) -> None:
        # Match admission lock order so ledger/reservation reads cannot miss a reconciliation.
        self.db.scalar(select(Workspace).where(Workspace.id == workspace_id).with_for_update())
        reservation = self.db.scalar(select(ModelCallReservation).where(
            ModelCallReservation.workspace_id == workspace_id,
            ModelCallReservation.id == reservation_id).with_for_update()
            .execution_options(populate_existing=True))
        if reservation is None:
            raise ValueError("Workspace reservation was not found")
        if reservation.status != "reserved":
            if (reservation.ai_run_id == ai_run_id
                    and reservation.status in {"released", "consumed"}):
                self.db.rollback()
                return
            raise ValueError("Reservation is already finalized")
        if ai_run_id is not None:
            ledger = self.db.scalar(select(AIRun).where(
                AIRun.workspace_id == workspace_id, AIRun.graph_run_id == reservation.graph_run_id,
                AIRun.id == ai_run_id))
            if ledger is None:
                raise ValueError("Reservation AI run was not found")
        reservation.ai_run_id = ai_run_id
        reservation.status = "reserved" if uncertain else ("consumed" if ai_run_id else "released")
        reservation.finalized_at = None if uncertain else datetime.now(UTC)
        self.db.commit()
