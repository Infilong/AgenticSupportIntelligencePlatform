from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_PASSWORD = "complex-demo-password"


class ApiError(RuntimeError):
    def __init__(self, method: str, path: str, status: int, body: str):
        super().__init__(f"{method} {path} failed with {status}: {body}")
        self.status = status
        self.body = body


def request_json(
    base_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    expected: tuple[int, ...] = (200,),
) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}", data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            if response.status not in expected:
                raise ApiError(method, path, response.status, body)
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        if exc.code not in expected:
            raise ApiError(method, path, exc.code, body) from exc
        return json.loads(body) if body else None


def ensure_user(base_url: str, email: str, password: str) -> str:
    register_payload = {
        "email": email,
        "password": password,
        "display_name": "Complex Demo Operator",
    }
    try:
        request_json(
            base_url,
            "POST",
            "/api/v1/auth/register",
            payload=register_payload,
            expected=(201,),
        )
    except ApiError as exc:
        if exc.status != 409:
            raise
    login = request_json(
        base_url,
        "POST",
        "/api/v1/auth/login",
        payload={"email": email, "password": password},
    )
    return str(login["access_token"])


def ensure_workspace(base_url: str, token: str, name: str) -> dict[str, Any]:
    workspaces = request_json(base_url, "GET", "/api/v1/workspaces", token=token)
    for workspace in workspaces:
        if workspace["name"] == name:
            return workspace
    return request_json(
        base_url,
        "POST",
        "/api/v1/workspaces",
        token=token,
        payload={"name": name},
        expected=(201,),
    )


def upload_documents(
    base_url: str, token: str, workspace_id: str, documents: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    uploaded = []
    existing = request_json(
        base_url,
        "GET",
        f"/api/v1/workspaces/{workspace_id}/knowledge-documents?limit=500",
        token=token,
    )
    existing_titles = {document["title"] for document in existing["items"]}
    for document in documents:
        if document["title"] in existing_titles:
            uploaded.append({"title": document["title"], "status": "already_present"})
            continue
        response = request_json(
            base_url,
            "POST",
            f"/api/v1/workspaces/{workspace_id}/knowledge-documents",
            token=token,
            payload=document,
            expected=(201,),
        )
        uploaded.append(
            {
                "title": response["document"]["title"],
                "chunks": response["chunk_count"],
                "embeddings": response["embedding_count"],
            }
        )
    return uploaded


def verify_retrieval(
    base_url: str, token: str, workspace_id: str, checks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    results = []
    for check in checks:
        response = request_json(
            base_url,
            "POST",
            f"/api/v1/workspaces/{workspace_id}/retrieval/search",
            token=token,
            payload={
                "query": check["query"],
                "language": check["language"],
                "top_k": check.get("top_k", 3),
                "min_score": check.get("min_score", 0.2),
            },
        )
        passed, evidence = evaluate_retrieval_check(check, response)
        results.append(
            {
                "name": check["name"],
                "passed": passed,
                "trace_id": response["trace_id"],
                "no_source": response["no_source"],
                "top_document": evidence.get("document_title"),
                "top_score": evidence.get("combined_score"),
                "citation": evidence.get("citation"),
            }
        )
    return results


def evaluate_retrieval_check(
    check: dict[str, Any], response: dict[str, Any]
) -> tuple[bool, dict[str, Any]]:
    if check.get("expected_no_source"):
        return response["no_source"] is True and not response["results"], {}
    if response["no_source"] or not response["results"]:
        return False, {}
    top = response["results"][0]
    text = top["content"]
    passed = top["document_title"] == check["expected_document"]
    passed = passed and all(fragment in text for fragment in check.get("must_include", []))
    return passed, top


def ensure_agent(base_url: str, token: str, workspace_id: str, name: str) -> dict[str, Any]:
    agents = request_json(
        base_url, "GET", f"/api/v1/workspaces/{workspace_id}/agents?limit=100", token=token
    )
    for agent in agents["items"]:
        if agent["name"] == name and agent["active"]:
            return agent
    return request_json(
        base_url,
        "POST",
        f"/api/v1/workspaces/{workspace_id}/agents",
        token=token,
        payload={"name": name, "token_budget": 4000},
        expected=(201,),
    )


def verify_agent(
    base_url: str,
    token: str,
    workspace_id: str,
    agent: dict[str, Any],
    check: dict[str, Any],
) -> dict[str, Any]:
    run = request_json(
        base_url,
        "POST",
        f"/api/v1/workspaces/{workspace_id}/agents/{agent['id']}/runs",
        token=token,
        payload={"input_message": check["input_message"]},
        expected=(201,),
    )
    trace = request_json(
        base_url,
        "GET",
        f"/api/v1/workspaces/{workspace_id}/agent-runs/{run['id']}/trace",
        token=token,
    )
    final_answer = run.get("final_answer") or ""
    return {
        "passed": (
            run["status"] == check["expected_status"]
            and run["language"] == check["expected_language"]
            and all(fragment in final_answer for fragment in check.get("must_include", []))
            and len(trace["steps"]) >= 7
            and len(trace["ai_runs"]) >= 2
        ),
        "run_id": run["id"],
        "status": run["status"],
        "language": run["language"],
        "route_decision": run["route_decision"],
        "step_count": len(trace["steps"]),
        "ai_run_count": len(trace["ai_runs"]),
        "final_answer": final_answer,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed and verify a complex knowledge base.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--fixture", default="demo/complex_knowledge_base.json")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    started = time.perf_counter()
    email = args.email or f"complex-demo+{int(time.time())}@example.com"
    token = ensure_user(args.base_url, email, args.password)
    workspace = ensure_workspace(args.base_url, token, fixture["workspace_name"])
    uploads = upload_documents(args.base_url, token, workspace["id"], fixture["documents"])
    retrieval = verify_retrieval(args.base_url, token, workspace["id"], fixture["retrieval_checks"])
    agent = ensure_agent(args.base_url, token, workspace["id"], fixture["agent_name"])
    agent_result = verify_agent(args.base_url, token, workspace["id"], agent, fixture["agent_check"])

    report = {
        "account": {"email": email, "password": args.password},
        "workspace": {"id": workspace["id"], "name": workspace["name"]},
        "uploads": uploads,
        "retrieval": retrieval,
        "agent": agent_result,
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    all_passed = all(item["passed"] for item in retrieval) and agent_result["passed"]
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
