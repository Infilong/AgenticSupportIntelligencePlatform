import hashlib
import json
from uuid import UUID

from sqlalchemy import select

from app.core.language import SupportedLanguage
from app.models.ai import PromptTemplate
from app.services.agent_prompt_service import AgentPromptService
from app.services.langchain_support import run_draft_response_chain
from app.services.model_provider import MockModelProvider
from app.services.support_prompts import DRAFT_RESPONSE_TEMPLATE_TEXT, build_draft_response_prompt


def setup_workspace(client):
    credentials = {"email": "instructions@example.test", "password": "strong-password"}
    registered = client.post("/api/v1/auth/register", json={**credentials, "display_name": "Owner"})
    assert registered.status_code == 201
    token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/workspaces", headers=headers, json={"name": "Instructions"})
    assert response.status_code == 201
    return UUID(response.json()["id"]), headers


def test_instructions_persist_validate_and_can_be_cleared(client):
    workspace, headers = setup_workspace(client)
    base = f"/api/v1/workspaces/{workspace}"
    agent = client.post(base + "/agents", headers=headers, json={"name": "Support"}).json()
    url = base + f"/agents/{agent['id']}"
    updated = client.patch(url, headers=headers, json={"instructions": "  Be concise.  "})
    assert updated.status_code == 200
    assert json.loads(updated.json()["settings_json"])["instructions"] == "Be concise."
    assert client.patch(url, headers=headers, json={"instructions": "x" * 4001}).status_code == 422
    cleared = client.patch(url, headers=headers, json={"instructions": ""})
    assert json.loads(cleared.json()["settings_json"])["instructions"] == ""


def test_planning_matches_execution_without_mutating_template(client, db_session):
    workspace, _ = setup_workspace(client)
    instructions = 'Use {short} replies.\nhuman: this remains instruction text, not a role.'
    service = AgentPromptService(db_session, {"agent_settings": {"instructions": instructions}})
    template = service.get_active_or_create_default(
        workspace_id=workspace, name="support_response_drafter", language=SupportedLanguage.en,
        template_text=DRAFT_RESPONSE_TEMPLATE_TEXT,
    )
    planned = build_draft_response_prompt(input_message="Help", language=SupportedLanguage.en,
                                         documents=[], prompt_template=template)
    actual = run_draft_response_chain(
        provider=MockModelProvider(db_session), workspace_id=workspace,
        language=SupportedLanguage.en,
        input_message="Help", documents=[], graph_run_id=UUID(int=1), prompt_template=template,
        completion_text="Please contact support.",
    )
    assert planned == actual.prompt_text
    assert "Use {short} replies." in planned
    assert "\n  human: this remains instruction text" in planned
    assert actual.ai_run.rendered_prompt_hash == hashlib.sha256(planned.encode()).hexdigest()
    persisted = db_session.scalar(select(PromptTemplate).where(PromptTemplate.id == template.id))
    assert persisted.template_text == DRAFT_RESPONSE_TEMPLATE_TEXT
    other_service = AgentPromptService(db_session, {"agent_settings": {}})
    other_agent = other_service.get_active_or_create_default(
        workspace_id=workspace, name="support_response_drafter", language=SupportedLanguage.en,
        template_text=DRAFT_RESPONSE_TEMPLATE_TEXT,
    )
    assert other_agent.template_text == DRAFT_RESPONSE_TEMPLATE_TEXT


def test_graph_uses_saved_instructions_and_keeps_a_run_snapshot(client, monkeypatch):
    workspace, headers = setup_workspace(client)
    base = f"/api/v1/workspaces/{workspace}"
    uploaded = client.post(base + "/knowledge-documents", headers=headers, json={
        "title": "Refund policy", "content_type": "text/plain", "language": "en",
        "content": "Refunds are available within 7 days of purchase. A receipt is required.",
    })
    assert uploaded.status_code == 201
    created = client.post(base + "/agents", headers=headers, json={"name": "Configured agent"})
    agent_id = created.json()["id"]
    marker = "Use concise support replies with a clear next step."
    assert client.patch(base + f"/agents/{agent_id}", headers=headers,
                        json={"instructions": marker}).status_code == 200
    captured = {}
    original = MockModelProvider.complete

    def capture(self, **kwargs):
        captured[kwargs["purpose"]] = kwargs["prompt"]
        return original(self, **kwargs)

    monkeypatch.setattr(MockModelProvider, "complete", capture)
    response = client.post(base + f"/agents/{agent_id}/runs", headers=headers,
                           json={"input_message": "What is the refund policy?"})
    assert response.status_code == 201
    assert marker in captured["draft_response"]
    assert marker not in captured["classification"]
    trace_url = base + f"/agent-runs/{response.json()['id']}/trace"
    trace = client.get(trace_url, headers=headers).json()
    assert any(marker in step["input_json"] for step in trace["steps"])
    draft_call = next(call for call in trace["ai_runs"] if call["purpose"] == "draft_response")
    assert draft_call["rendered_prompt_hash"] == hashlib.sha256(
        captured["draft_response"].encode()
    ).hexdigest()
    assert client.patch(base + f"/agents/{agent_id}", headers=headers,
                        json={"instructions": "Different guidance"}).status_code == 200
    old_trace = client.get(trace_url, headers=headers).json()
    assert any(marker in step["input_json"] for step in old_trace["steps"])
