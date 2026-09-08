import json
import urllib.request
from uuid import UUID

import pytest
from sqlalchemy import select
from test_graph_budget_enforcement import graph_budget_context as graph_budget_context
from test_graph_budget_enforcement import run

from app.core.config import get_settings
from app.core.language import SupportedLanguage
from app.models.ai import ModelConfig
from app.models.reservation import ModelCallReservation
from app.services.budgeted_model_provider import BudgetedModelProvider
from app.services.model_provider import MockModelProvider, ModelProviderError
from app.services.openai_transport import UrllibOpenAIChatTransport


def prepare(client, db, context, monkeypatch, *, real=True):
    result = run(client, context)
    workspace_id, graph_run_id = UUID(context[1]), UUID(result["id"])
    if real:
        db.add(ModelConfig(workspace_id=workspace_id, provider="openai", model="test-chat",
                           purpose="draft_response", active=True,
                           prompt_token_cost_per_1k=0.0001,
                           completion_token_cost_per_1k=0.0002, max_context_tokens=8192))
        db.commit()
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    get_settings.cache_clear()
    return dict(workspace_id=workspace_id, graph_run_id=graph_run_id, purpose="draft_response",
                prompt="Policy?", completion_text="Policy answer", language=SupportedLanguage.en)


def test_real_transport_receives_reserved_output_cap(client, db_session, graph_budget_context,
                                                    monkeypatch):
    args = prepare(client, db_session, graph_budget_context, monkeypatch)
    requests = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "Policy answer"}}],
                               "usage": {"prompt_tokens": 12, "completion_tokens": 2}}).encode()

    def transport(request, **kwargs):
        requests.append(json.loads(request.data))
        reservation = db_session.scalar(select(ModelCallReservation).where(
            ModelCallReservation.purpose == "draft_response"))
        assert reservation.status == "reserved" and reservation.ai_run_id is None
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", transport)
    result = BudgetedModelProvider(db_session).complete(**args)
    assert requests[0]["max_completion_tokens"] == 1024
    reservation = db_session.scalar(select(ModelCallReservation).where(
        ModelCallReservation.ai_run_id == result.ai_run.id))
    assert reservation.status == "consumed"
    assert reservation.estimated_tokens == len(args["prompt"].encode()) + 32 + 1024


def test_timeout_retains_allowance_for_uncertain_usage(client, db_session, graph_budget_context,
                                                       monkeypatch):
    args = prepare(client, db_session, graph_budget_context, monkeypatch)

    def timeout(*args, **kwargs):
        raise TimeoutError("synthetic timeout")

    monkeypatch.setattr(urllib.request, "urlopen", timeout)
    with pytest.raises(ModelProviderError):
        BudgetedModelProvider(db_session).complete(**args)
    reservation = db_session.scalar(select(ModelCallReservation).where(
        ModelCallReservation.purpose == "draft_response"))
    assert reservation.status == "reserved" and reservation.ai_run_id is not None


def test_known_mock_preledger_failure_releases_reservation(client, db_session, graph_budget_context,
                                                          monkeypatch):
    args = prepare(client, db_session, graph_budget_context, monkeypatch, real=False)

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic preledger failure")

    monkeypatch.setattr(MockModelProvider, "complete", fail)
    with pytest.raises(RuntimeError, match="synthetic preledger failure"):
        BudgetedModelProvider(db_session).complete(**args)
    reservation = db_session.scalar(select(ModelCallReservation).where(
        ModelCallReservation.purpose == "draft_response"))
    assert reservation.status == "released" and reservation.ai_run_id is None


@pytest.mark.parametrize("usage", [None, {"prompt_tokens": 12}, {"completion_tokens": 2}])
def test_missing_usage_retains_reservation(client, db_session, graph_budget_context,
                                          monkeypatch, usage):
    args = prepare(client, db_session, graph_budget_context, monkeypatch)
    monkeypatch.setattr(UrllibOpenAIChatTransport, "create_chat_completion", lambda *a, **kw: {
        "choices": [{"message": {"content": "Answer"}}], "usage": usage,
    })
    response = BudgetedModelProvider(db_session).complete(**args)
    reservation = db_session.scalar(select(ModelCallReservation).where(
        ModelCallReservation.ai_run_id == response.ai_run.id))
    assert not response.usage_complete
    assert reservation.status == "reserved"


@pytest.mark.parametrize("usage", [
    {"prompt_tokens": -1, "completion_tokens": 2},
    {"prompt_tokens": 1.5, "completion_tokens": 2},
])
def test_invalid_usage_does_not_free_allowance(client, db_session, graph_budget_context,
                                             monkeypatch, usage):
    args = prepare(client, db_session, graph_budget_context, monkeypatch)
    monkeypatch.setattr(UrllibOpenAIChatTransport, "create_chat_completion", lambda *a, **kw: {
        "choices": [{"message": {"content": "Answer"}}], "usage": usage,
    })
    with pytest.raises(ModelProviderError):
        BudgetedModelProvider(db_session).complete(**args)
    row = db_session.scalar(select(ModelCallReservation).where(
        ModelCallReservation.purpose == "draft_response"))
    assert row.status == "reserved" and row.ai_run_id is not None
