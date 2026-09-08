"""Model calls reserve shared budgets before dispatch, then reconcile their ledger."""

from dataclasses import replace
from typing import Any

from sqlalchemy.orm import Session

from app.services.budget_reservations import BudgetReservationDenied, BudgetReservationService
from app.services.model_config_service import ModelConfigService
from app.services.model_provider import ConfiguredModelProvider, ModelProviderError
from app.services.token_accounting import estimate_cost
from app.services.token_budget import TokenBudgetPlanner


class ModelBudgetDenied(ModelProviderError):
    budget_denial = True


class BudgetedModelProvider:
    def __init__(self, db: Session):
        self.db = db
        self.provider = ConfiguredModelProvider(db)

    def complete(self, **kwargs: Any):
        evaluation_run_id = kwargs.pop("evaluation_run_id", None)
        pricing = ModelConfigService(self.db).resolve_pricing(
            workspace_id=kwargs["workspace_id"], purpose=kwargs["purpose"],
            fallback_model=kwargs.get("model", "mock-standard"),
            model_config_id=kwargs.get("model_config_id"),
        )
        plan = TokenBudgetPlanner().plan_model_call(
            prompt_text=kwargs["prompt"], completion_text=kwargs.get("completion_text", ""),
            language=kwargs["language"], pricing=pricing,
        )
        real = pricing.provider.strip().lower() in {"openai", "openai-compatible"}
        if real:
            # Conservative text allowance; not a universal provider tokenizer/billing guarantee.
            prompt_tokens = len(kwargs["prompt"].encode("utf-8")) + 32
            completion_tokens = 512 if kwargs["purpose"] == "classification" else 1024
            total = prompt_tokens + completion_tokens
            plan = replace(plan, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                           total_tokens=total, allowed=total <= pricing.max_context_tokens,
                           estimated_cost=estimate_cost(
                               prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                               prompt_token_cost_per_1k=pricing.prompt_token_cost_per_1k,
                               completion_token_cost_per_1k=pricing.completion_token_cost_per_1k))
        service = BudgetReservationService(self.db)
        try:
            reservation = service.reserve(
                workspace_id=kwargs["workspace_id"], graph_run_id=kwargs.get("graph_run_id"),
                evaluation_run_id=evaluation_run_id,
                purpose=kwargs["purpose"], plan=plan,
                lifetime_seconds=max(300, self.provider.openai_provider.timeout_seconds + 60),
            )
        except BudgetReservationDenied as exc:
            raise ModelBudgetDenied(exc.reason) from exc
        try:
            if real:
                response = self.provider.openai_provider.complete_with_pricing(
                    pricing=pricing, max_completion_tokens=plan.completion_tokens, **kwargs)
            else:
                response = self.provider.mock_provider.complete(**kwargs)
        except ModelProviderError as exc:
            if exc.ai_run is not None:
                # Provider errors can hide billed usage; retain allowance until reconciliation.
                uncertain = real and str(exc).startswith("openai_provider_error:")
                service.finalize(workspace_id=kwargs["workspace_id"],
                                 reservation_id=reservation.id, ai_run_id=exc.ai_run.id,
                                 uncertain=uncertain)
            elif not real:
                service.finalize(workspace_id=kwargs["workspace_id"], reservation_id=reservation.id)
            raise
        except Exception:
            # A real dispatch without a ledger has unknown usage; do not release it prematurely.
            if not real:
                service.finalize(workspace_id=kwargs["workspace_id"], reservation_id=reservation.id)
            raise
        service.finalize(workspace_id=kwargs["workspace_id"], reservation_id=reservation.id,
                         ai_run_id=response.ai_run.id,
                         uncertain=real and not response.usage_complete)
        if (response.ai_run.total_tokens > plan.total_tokens
                or response.ai_run.estimated_cost > plan.estimated_cost + 0.00000001):
            raise ModelProviderError("provider_usage_exceeded_reservation", ai_run=response.ai_run)
        return response
