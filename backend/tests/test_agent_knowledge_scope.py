import json

from sqlalchemy import select
from test_admin_hierarchy import account

from app.models.retrieval import RetrievalTrace
from app.services.model_provider import MockModelProvider


def fixture(client):
    _, _, headers = account(client, "knowledge-owner")
    workspace = client.post("/api/v1/workspaces", headers=headers,
                            json={"name": "Agent knowledge"}).json()["id"]
    base = f"/api/v1/workspaces/{workspace}"
    agent = client.post(base + "/agents", headers=headers, json={"name": "Support"}).json()["id"]
    documents = []
    for title, content in [("Public refund", "Refunds within 7 days require a receipt."),
                           ("Restricted refund", "Refund exception secret-internal-marker123.")]:
        uploaded = client.post(base + "/knowledge-documents", headers=headers, json={
            "title": title, "content": content, "language": "en", "content_type": "text/plain"})
        assert uploaded.status_code == 201
        documents.append(uploaded.json()["document"]["id"])
    return base, agent, documents, headers


def test_scope_validation_deduplicates_and_can_be_cleared(client):
    base, agent, documents, headers = fixture(client)
    url = base + f"/agents/{agent}"
    selected = client.patch(url, headers=headers,
                            json={"knowledge_document_ids": [documents[0], documents[0]]})
    assert selected.status_code == 200
    assert json.loads(selected.json()["settings_json"])["knowledge_document_ids"] == documents[:1]
    assert client.patch(url, headers=headers,
                         json={"knowledge_document_ids": documents[:1] * 101}).status_code == 422
    other = client.post("/api/v1/workspaces", headers=headers,
                        json={"name": "Other workspace"}).json()["id"]
    foreign = client.post(f"/api/v1/workspaces/{other}/agents", headers=headers,
                          json={"name": "Foreign"}).json()["id"]
    assert client.patch(f"/api/v1/workspaces/{other}/agents/{foreign}", headers=headers,
                         json={"knowledge_document_ids": documents}).status_code == 404
    cleared = client.patch(url, headers=headers, json={"knowledge_document_ids": None})
    assert json.loads(cleared.json()["settings_json"])["knowledge_document_ids"] is None


def test_graph_scope_excludes_unselected_text_and_empty_scope_provides_no_evidence(
    client, db_session, monkeypatch,
):
    base, agent, documents, headers = fixture(client)
    url = base + f"/agents/{agent}"
    prompts = []
    complete = MockModelProvider.complete

    def capture(self, **kwargs):
        prompts.append(kwargs["prompt"])
        return complete(self, **kwargs)

    monkeypatch.setattr(MockModelProvider, "complete", capture)
    for scope in [documents[:1], []]:
        assert client.patch(url, headers=headers,
                             json={"knowledge_document_ids": scope}).status_code == 200
        response = client.post(url + "/runs", headers=headers,
                                json={"input_message": "What is the refund policy?"})
        assert response.status_code == 201
        trace_url = base + f"/agent-runs/{response.json()['id']}/trace"
        trace = client.get(trace_url, headers=headers).json()
        retrieval = next(step for step in trace["steps"]
                         if step["step_name"] == "retrieve_evidence")
        chunks = json.loads(retrieval["output_json"])["retrieved_chunks"]
        assert {chunk["document_id"] for chunk in chunks} == set(scope)
        if not scope:
            assert response.json()["status"] == "needs_human_review"
            assert response.json()["final_answer"] is None
    assert all("secret-internal-marker123" not in prompt for prompt in prompts)
    filters = [json.loads(trace.filters_json)
               for trace in db_session.scalars(select(RetrievalTrace))]
    assert [item["allowed_document_ids"] for item in filters] == [documents[:1], []]
