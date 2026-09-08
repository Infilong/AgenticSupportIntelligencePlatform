from uuid import uuid4

from test_record_clarifications import waiting

from app.models.review import HumanReview


def test_record_review_lookup_is_scoped_to_input_and_attempt(client, db_session):
    base, headers, record, run = waiting(client, db_session)
    url = base + f"/records/{record['id']}/attempts/{run.id}/review"
    assert client.get(url, headers=headers).json() is None
    review = HumanReview(workspace_id=run.workspace_id, graph_run_id=run.id,
        reason="Policy exception", proposed_answer="Needs a decision", reviewer_decision="pending")
    db_session.add(review)
    db_session.commit()
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(review.id)
    assert response.json()["proposed_answer"] == "Needs a decision"
    assert client.get(url).status_code == 401
    assert client.get(url.replace(record["id"], str(uuid4())), headers=headers).status_code == 404
    second = client.post("/api/v1/workspaces", headers=headers, json={"name": "Other"}).json()["id"]
    foreign = url.replace(str(run.workspace_id), second)
    assert client.get(foreign, headers=headers).status_code == 404
