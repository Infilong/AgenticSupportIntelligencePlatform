"""Real local API→worker→CPU model smoke; the full corpus quality gate is separate."""

import hashlib
import json
import time
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]


def main():
    credentials = json.loads((ROOT / ".artifacts/m1/demo-credentials.json").read_text(encoding="utf-8"))
    original = (ROOT / "evals/fixtures/policies/refunds-en-v2.md").read_bytes()
    checksum = hashlib.sha256(original).hexdigest()
    with httpx.Client(base_url="http://127.0.0.1:8010", timeout=20) as client:
        csrf = client.get("/api/session").json()["csrf_token"]
        headers = {"Origin": "http://127.0.0.1:5180", "X-CSRF-Token": csrf}
        response = client.post(
            "/api/session/login",
            headers=headers,
            json={"email": credentials["accounts"]["admin"], "password": credentials["password"]},
        )
        response.raise_for_status()
        headers["X-CSRF-Token"] = response.json()["csrf_token"]
        workspace = client.get("/api/workspaces").json()[0]["id"]
        headers["Idempotency-Key"] = "real-ingestion-smoke-" + uuid.uuid4().hex
        response = client.post(
            f"/api/workspaces/{workspace}/documents",
            headers=headers,
            files={"file": ("Refund policy — CPU ingestion smoke.md", original)},
        )
        response.raise_for_status()
        uploaded = response.json()
        path = f"/api/workspaces/{workspace}/documents/{uploaded['document_id']}"
        for _ in range(120):
            detail_response = client.get(path)
            detail_response.raise_for_status()
            detail = detail_response.json()
            status = detail["document"]["job_status"]
            if status in {"succeeded", "failed", "cancelled"}:
                if status != "succeeded":
                    raise RuntimeError("Real ingestion failed: " + str(detail["document"]["error_code"]))
                version_path = f"{path}/versions/{uploaded['version_id']}"
                downloaded = client.get(version_path + "/original")
                downloaded.raise_for_status()
                preview = client.get(version_path).json()
                assert downloaded.content == original
                assert preview["active"] and preview["checksum"] == checksum
                print(
                    json.dumps(
                        {
                            "status": "real_ingestion_passed",
                            **uploaded,
                            "workspace_id": workspace,
                            "original_bytes": len(original),
                            "checksum": checksum,
                            "quality_gate": "not_evaluated",
                        }
                    )
                )
                client.post("/api/session/logout", headers=headers).raise_for_status()
                return 0
            time.sleep(1)
        raise TimeoutError("Document did not finish indexing within 120 seconds")


if __name__ == "__main__":
    raise SystemExit(main())
