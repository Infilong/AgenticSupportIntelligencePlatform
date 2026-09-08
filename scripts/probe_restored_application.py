"""Run API contracts against a disposable restore containing multilingual journey fixtures."""

import json
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal, engine
from app.main import app
from app.models.agent import AgentConfig, GraphRun
from app.models.user import User
from app.models.workspace import Workspace
from app.services.task_worker import execute_task


def main():
    assert engine.url.database.startswith("asi_restore_"), "Refusing non-restore database"
    checks = []
    with SessionLocal() as db, TestClient(app) as client:
        for language, fact in (("en", "7 days"), ("ja", "7日"), ("zh", "7天")):
            user = db.scalar(select(User).where(
                User.email.like(f"journey-{language}-%@example.test")
            ).order_by(User.created_at.desc()).limit(1))
            assert user is not None, "Run multilingual-workflow.spec.ts before this drill"
            workspace = db.scalar(select(Workspace).where(
                Workspace.created_by_user_id == user.id, Workspace.name.like("Journey %")))
            assert workspace is not None
            agent = db.scalar(select(AgentConfig).where(AgentConfig.workspace_id == workspace.id))
            old_run = db.scalar(select(GraphRun).where(
                GraphRun.workspace_id == workspace.id, GraphRun.status == "completed",
            ).order_by(GraphRun.created_at.desc()).limit(1))
            assert agent is not None and old_run is not None
            login = client.post("/api/v1/auth/login", json={
                "email": user.email, "password": "synthetic-strong-password"})
            assert login.status_code == 200, "Restored password login failed"
            headers = {"Authorization": "Bearer " + login.json()["access_token"]}
            base = f"/api/v1/workspaces/{workspace.id}"
            assert client.get(base + "/datasets", headers=headers).status_code == 200
            assert client.get(base + "/knowledge-documents", headers=headers).status_code == 200
            trace = client.get(base + f"/agent-runs/{old_run.id}/trace", headers=headers)
            assert trace.status_code == 200 and trace.json()["steps"] and trace.json()["ai_runs"]
            assert client.get(base + "/human-reviews", headers=headers).json()["items"]
            evaluations = client.get(base + "/evaluations", headers=headers)
            assert evaluations.status_code == 200 and evaluations.json()
            costs = client.get(base + "/costs/summary", headers=headers)
            assert costs.status_code == 200 and costs.json()["total_tokens"] > 0
            assert client.get(base + "/knowledge-documents").status_code == 401
            foreign = db.scalar(select(Workspace).where(Workspace.created_by_user_id != user.id))
            assert foreign is not None
            assert client.get(f"/api/v1/workspaces/{foreign.id}/knowledge-documents",
                              headers=headers).status_code == 404
            payload = {"agent_id": str(agent.id), "input_message": old_run.input_message,
                       "request_key": "restore-" + uuid4().hex, "language": language}
            result = client.post(base + "/tasks", headers=headers, json=payload)
            assert result.status_code == 202
            admitted = result.json()
            run_id = admitted["run"]["id"]
            assert admitted["task_id"] and admitted["run"]["status"] == "queued"
            replay = client.post(base + "/tasks", headers=headers, json=payload)
            assert replay.status_code == 202 and replay.json()["run"]["id"] == run_id
            assert execute_task(engine, workspace_id=workspace.id,
                                run_id=UUID(run_id)) == "completed"
            read = client.get(base + f"/task-runs/{run_id}", headers=headers)
            assert read.status_code == 200 and read.json()["task_id"] == admitted["task_id"]
            run = read.json()["run"]
            attempts = client.get(base + f"/task-runs/{run_id}/attempts", headers=headers)
            assert attempts.status_code == 200 and attempts.json()["total"] == 1
            assert client.get(base + f"/task-runs/{run_id}").status_code == 401
            assert client.get(f"/api/v1/workspaces/{foreign.id}/task-runs/{run_id}",
                              headers=headers).status_code == 404
            assert run["status"] == "completed" and run["language"] == language
            assert fact in run["final_answer"] and "#chunk-" in run["final_answer"]
            new_trace = client.get(base + f"/agent-runs/{run['id']}/trace", headers=headers).json()
            assert len(new_trace["ai_runs"]) == 2
            assert all(row["provider"] == "mock" for row in new_trace["ai_runs"])
            assert any(row["step_name"] == "retrieve_evidence" for row in new_trace["steps"])
            payload["request_key"] = "restore-stop-" + uuid4().hex
            queued = client.post(base + "/tasks", headers=headers, json=payload)
            assert queued.status_code == 202
            stopped_id = queued.json()["run"]["id"]
            stopped = client.post(base + f"/task-runs/{stopped_id}/stop", headers=headers)
            assert stopped.status_code == 200 and stopped.json()["status"] == "stopped"
            assert execute_task(engine, workspace_id=workspace.id,
                                run_id=UUID(stopped_id)) == "stopped"
            stopped_trace = client.get(base + f"/agent-runs/{stopped_id}/trace",
                                       headers=headers).json()
            assert not stopped_trace["ai_runs"]
            actions = client.get(base + f"/task-runs/{stopped_id}/actions", headers=headers)
            assert actions.status_code == 200 and actions.json() == []
            original = {"format": "json", "content": {"question": old_run.input_message,
                        "reference": "restore-native-record"}, "source": "admin",
                        "source_reference": "restore-native-record"}
            record_payload = {"agent_id": str(agent.id), "input": original,
                              "request_key": "restore-record-" + uuid4().hex,
                              "language": language}
            created = client.post(base + "/records", headers=headers, json=record_payload)
            assert created.status_code == 202
            record = created.json()
            assert record["input"] == original and record["status"] == "queued"
            duplicate = client.post(base + "/records", headers=headers, json=record_payload)
            assert duplicate.status_code == 202 and duplicate.json()["id"] == record["id"]
            assert execute_task(engine, workspace_id=workspace.id,
                                run_id=UUID(record["latest_run_id"])) == "completed"
            detail = client.get(base + f"/records/{record['id']}", headers=headers)
            assert detail.status_code == 200 and detail.json()["input"] == original
            assert detail.json()["attempt_count"] == 1
            artifacts = client.get(base + f"/records/{record['id']}/attempts/"
                + record["latest_run_id"] + "/artifacts", headers=headers)
            assert artifacts.status_code == 200 and artifacts.json()["items"]
            assert client.get(base + f"/records/{record['id']}").status_code == 401
            assert client.get(f"/api/v1/workspaces/{foreign.id}/records/{record['id']}",
                              headers=headers).status_code == 404
            checks.append({"language": language,
                           "restored_login_reads_isolation_durable_run_replay_and_stop": "passed",
                           "native_records_originals_replay_artifacts_and_isolation": "passed"})
    engine.dispose()
    print(json.dumps({"status": "passed", "checks": checks}))


if __name__ == "__main__":
    main()
