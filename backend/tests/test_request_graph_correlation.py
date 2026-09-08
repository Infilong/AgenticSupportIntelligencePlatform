import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_agents import auth_headers, create_agent, create_workspace, login, register

from app.core.request_context import request_id_context
from app.core.request_logging import RequestLogMiddleware
from app.core.workflow_logging import log_graph_created
from app.models.agent import GraphRun
from app.services.support_agent_graph import SupportAgentGraphRunner


@pytest.fixture
def captured_events(caplog):
    loggers = [logging.getLogger(name) for name in ("asi.http", "asi.workflow")]
    for logger in loggers:
        logger.addHandler(caplog.handler)
    yield lambda: [json.loads(record.message) for record in caplog.records
                   if record.name in {"asi.http", "asi.workflow"}]
    for logger in loggers:
        logger.removeHandler(caplog.handler)


@pytest.mark.parametrize("mode", ["success", "failure", "denied"])
def test_real_agent_request_links_persisted_run_without_content(
    client, db_session, monkeypatch, captured_events, mode,
):
    register(client, "request-link@example.test")
    token = login(client, "request-link@example.test")
    workspace = create_workspace(client, token)
    agent = create_agent(client, token, workspace["id"])
    if mode == "failure":
        def fail(self, state):
            raise RuntimeError("private provider error")
        monkeypatch.setattr(SupportAgentGraphRunner, "run", fail)
    headers = auth_headers(token) if mode != "denied" else {}
    headers["X-Request-ID"] = "untrusted-client-id"
    path = f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs"
    if mode == "failure":
        with pytest.raises(RuntimeError, match="private provider error"):
            client.post(path, headers=headers, json={"input_message": "Private customer refund?"})
    else:
        response = client.post(path, headers=headers,
                               json={"input_message": "Private customer refund?"})
        assert response.status_code == (401 if mode == "denied" else 201)
    events = captured_events()
    links = [row for row in events if row["event"] == "graph_run_created"]
    outcome = [row for row in events if row["event"] == "http_request"
               and row["route"].endswith("/runs")][-1]
    assert outcome["status"] == {"success": 201, "failure": 500, "denied": 401}[mode]
    if mode == "denied":
        assert links == []
    else:
        link, = links
        assert link["request_id"] == outcome["request_id"]
        run = db_session.get(GraphRun, UUID(link["graph_run_id"]))
        assert run is not None
        assert run.trace_id == link["trace_id"]
        assert set(link) == {"event", "request_id", "graph_run_id", "trace_id"}
        if mode == "success":
            assert response.headers["x-request-id"] == link["request_id"]
            assert response.json()["id"] == link["graph_run_id"]
    text = json.dumps(events)
    assert "Private customer" not in text
    assert "private provider error" not in text
    assert "untrusted-client-id" not in text
    assert token not in text


def test_concurrent_sync_workers_keep_distinct_request_context(captured_events):
    app = FastAPI()
    app.add_middleware(RequestLogMiddleware)
    ready = Barrier(2)

    @app.get("/start")
    def start():
        graph_id = uuid4()
        trace_id = str(uuid4())
        ready.wait(timeout=10)
        log_graph_created(graph_id, trace_id)
        return {"graph_run_id": str(graph_id), "trace_id": trace_id}

    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as pool:
        responses = [future.result(timeout=15) for future in
                     [pool.submit(client.get, "/start") for _ in range(2)]]
    links = [row for row in captured_events() if row["event"] == "graph_run_created"]
    assert len(links) == 2
    assert len({row["request_id"] for row in links}) == 2
    for response in responses:
        link, = [row for row in links if row["request_id"] == response.headers["x-request-id"]]
        assert response.json() == {key: link[key] for key in ("graph_run_id", "trace_id")}
    assert request_id_context.get() is None
    log_graph_created(uuid4(), str(uuid4()))
    assert len([row for row in captured_events() if row["event"] == "graph_run_created"]) == 2


def test_evaluation_graphs_share_only_the_enclosing_request(client, captured_events):
    register(client, "evaluation-links@example.test")
    token = login(client, "evaluation-links@example.test")
    workspace = create_workspace(client, token)
    agent = create_agent(client, token, workspace["id"])
    response = client.post(f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token), json={
            "name": "Correlation cases", "agent_id": agent["id"], "modes": ["system_v1"],
            "jsonl_cases": "\n".join(json.dumps({
                "id": str(index), "language": "en", "input_message": "Refund policy?",
            }) for index in range(2)),
        })
    assert response.status_code == 201
    links = [row for row in captured_events() if row["event"] == "graph_run_created"]
    assert len(links) == 2
    assert {row["request_id"] for row in links} == {response.headers["x-request-id"]}
    assert {row["graph_run_id"] for row in links} == {
        row["graph_run_id"] for row in response.json()["results"]
    }


@pytest.mark.parametrize("failed", [False, True])
def test_middleware_restores_enclosing_context_on_exit(captured_events, failed):
    async def application(scope, receive, send):
        assert request_id_context.get() != "enclosing-context"
        if failed:
            raise ValueError("synthetic failure")
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        pass

    async def exercise():
        previous = request_id_context.set("enclosing-context")
        try:
            operation = RequestLogMiddleware(application)(
                {"type": "http", "method": "GET", "path": "/"}, receive, send,
            )
            if failed:
                with pytest.raises(ValueError, match="synthetic failure"):
                    await operation
            else:
                await operation
            assert request_id_context.get() == "enclosing-context"
        finally:
            request_id_context.reset(previous)

    asyncio.run(exercise())
