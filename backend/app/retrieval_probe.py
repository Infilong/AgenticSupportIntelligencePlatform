"""Query actual local embeddings and PostgreSQL through the authenticated API."""

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]


def main():
    credentials = json.loads((ROOT / ".artifacts/m1/demo-credentials.json").read_text(encoding="utf-8"))
    with httpx.Client(base_url="http://127.0.0.1:8010", timeout=90) as client:
        csrf = client.get("/api/session").json()["csrf_token"]
        headers = {"Origin": "http://127.0.0.1:5180", "X-CSRF-Token": csrf}
        signed = client.post(
            "/api/session/login",
            headers=headers,
            json={
                "email": credentials["accounts"]["admin"],
                "password": credentials["password"],
            },
        )
        signed.raise_for_status()
        headers["X-CSRF-Token"] = signed.json()["csrf_token"]
        workspace = client.get("/api/workspaces").json()[0]["id"]
        result = client.post(
            f"/api/workspaces/{workspace}/retrieval",
            headers=headers,
            json={"query": "What is the standard refund request deadline?", "limit": 5},
        )
        result.raise_for_status()
        data = result.json()
        assert data["status"] == "candidates"
        assert any("14 calendar days" in row["text"] for row in data["results"])
        for row in data["results"]:
            source = client.get(
                f"/api/workspaces/{workspace}/documents/{row['document_id']}/versions/{row['version_id']}",
                params={"offset": row["start_offset"], "limit": row["end_offset"] - row["start_offset"]},
            )
            source.raise_for_status()
            assert source.json()["text"] == row["text"]
        print(
            json.dumps(
                {
                    "status": "real_retrieval_smoke_passed",
                    "trace_id": data["trace_id"],
                    "duration_ms": data["duration_ms"],
                    "candidates": len(data["results"]),
                    "quality_gate": "not_evaluated",
                }
            )
        )
        client.post("/api/session/logout", headers=headers).raise_for_status()


if __name__ == "__main__":
    main()
