from app.services.model_provider import ModelProviderError
from app.services.support_agent_state import SupportAgentState
from app.services.token_budget import ModelCallBudgetPlan


def _budget_failure_output(
    state: SupportAgentState, plan: ModelCallBudgetPlan, *, purpose: str
) -> SupportAgentState:
    message = (
        f"model_context_exceeded: {purpose} requested {plan.total_tokens} tokens "
        f"but {plan.model} allows {plan.max_context_tokens}"
    )
    errors = [*state.get("errors", []), message]
    return {
        "model_budget_failure": message,
        "errors": errors,
        "confidence_score": 0.0,
        "route_decision": "human_review",
    }


def _provider_failure_output(
    state: SupportAgentState, exc: ModelProviderError
) -> SupportAgentState:
    message = str(exc)
    errors = [*state.get("errors", []), message]
    return {
        ("model_budget_failure" if getattr(exc, "budget_denial", False)
         else "model_provider_failure"): message,
        "errors": errors,
        "confidence_score": 0.0,
        "route_decision": "human_review",
    }


