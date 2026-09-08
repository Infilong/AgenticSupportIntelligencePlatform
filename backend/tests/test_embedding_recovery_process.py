"""Terminate only a dedicated mock-dispatch worker and recover through the real API."""

import multiprocessing
import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.core.config import get_settings
from app.core.language import SupportedLanguage
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import create_app
from app.models.ai import AIRun, AIRunStatus
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.accounted_embeddings import AccountedEmbeddingProvider
from app.services.embedding_api import EmbeddingAPI
from app.services.embedding_attempts import EmbeddingAttemptLedger

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def _worker(url, schema, workspace, pipe, waiting):
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema},public"})

    class Transport:
        def create(self, **kwargs):
            with Session(engine) as db:
                attempt = db.scalar(select(AIRun))
                pipe.send(str(attempt.id))
            waiting.wait(60)
            raise RuntimeError("mock worker should have been terminated")

    try:
        AccountedEmbeddingProvider(
            api=EmbeddingAPI(api_key="synthetic", model="text-embedding-3-small", dimensions=1,
                             transport=Transport()), ledger=EmbeddingAttemptLedger(engine),
            workspace_id=UUID(workspace), language=SupportedLanguage.en,
            token_cost_per_1k=0.001, purpose="embedding_query").embed_texts(["refund policy"])
    finally:
        engine.dispose()


def test_api_rejects_live_worker_then_recovers_terminated_worker(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        db.add(WorkspaceMember(workspace_id=ids[0], user_id=ids[2][0], role=WorkspaceRole.owner))
        db.commit()
        schema = db.scalar(text("SELECT current_schema()"))
    context = multiprocessing.get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    waiting = context.Event()
    process = context.Process(target=_worker, args=(
        engine.url.render_as_string(hide_password=False), schema, str(ids[0]), send, waiting))
    app = create_app()

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database
    headers = {"Authorization": "Bearer " + create_access_token(str(ids[2][0]), get_settings())}
    process.start()
    try:
        assert receive.poll(20), "mock worker did not reach provider dispatch"
        attempt_id = receive.recv()
        assert process.is_alive()
        path = f"/api/v1/workspaces/{ids[0]}/embedding-attempts/{attempt_id}/recover"
        with TestClient(app) as client:
            live = client.post(path, headers=headers, json={"reason": "Investigate worker"})
            assert live.status_code == 409
            assert live.json()["detail"]["code"] == "embedding_execution_live"
            process.terminate()
            process.join(10)
            assert not process.is_alive() and process.exitcode is not None
            recovered = client.post(path, headers=headers, json={"reason": "Worker terminated"})
            assert recovered.status_code == 200, recovered.text
            assert recovered.json()["status"] == "uncertain"
            assert recovered.json()["total_tokens"] == 13
            assert recovered.json()["estimated_cost"] == pytest.approx(0.000013)
            assert client.post(path, headers=headers, json={"reason": "Repeat"}).status_code == 409
            reconciled = client.post(path.removesuffix("recover") + "reconcile", headers=headers,
                json={"confirmed_tokens": 2, "evidence_reference": "synthetic billing proof"})
            assert reconciled.status_code == 200
            assert reconciled.json()["status"] == "failed"
            assert reconciled.json()["total_tokens"] == 2
        with Session(engine) as db:
            assert db.get(AIRun, UUID(attempt_id)).status == AIRunStatus.failed
    finally:
        if process.is_alive():
            process.terminate()
        process.join(10)
        receive.close()
        send.close()
