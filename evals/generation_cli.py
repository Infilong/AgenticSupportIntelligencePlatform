"""Authenticated development comparison commands; never read scoring fixtures."""

import argparse
import json
import uuid
from pathlib import Path

import httpx

from generation_session import authenticate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["create", "list", "read", "export", "submit", "cancel"])
    parser.add_argument("--credentials", type=Path, required=True)
    parser.add_argument("--session", type=Path, help="Reuse a local session file under .artifacts")
    parser.add_argument("--workspace", type=uuid.UUID, required=True)
    parser.add_argument("--comparison", type=uuid.UUID)
    parser.add_argument("--pipeline", choices=["direct_llm", "vector_rag", "hybrid_rag", "system_v1"])
    parser.add_argument("--input", type=Path, help="Question/language for create; bound response for submit")
    parser.add_argument("--key", default=None, help="Persist and reuse this admission key for retries")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action not in {"create", "list"} and args.comparison is None:
        parser.error("--comparison is required")
    if args.action in {"export", "submit"} and args.pipeline is None:
        parser.error("--pipeline is required")
    if args.action in {"create", "submit"} and args.input is None:
        parser.error("--input is required")
    if args.action == "create" and not args.key:
        parser.error("--key is required for resumable admission")
    credentials = json.loads(args.credentials.read_text(encoding="utf-8"))
    if args.output.exists():
        parser.error("--output must be a new file")
    with httpx.Client(base_url="http://127.0.0.1:8010", timeout=120) as client:
        authenticate(client, credentials, args.session)
        path = f"/api/workspaces/{args.workspace}/comparisons"
        if args.comparison:
            path += f"/{args.comparison}"
        data = json.loads(args.input.read_text(encoding="utf-8")) if args.input else None
        if args.action == "create":
            response = client.post(path, json=data, headers={"Idempotency-Key": args.key})
        elif args.action == "export":
            response = client.get(f"{path}/{args.pipeline}/request")
        elif args.action == "submit":
            response = client.post(f"{path}/{args.pipeline}/response", json=data)
        elif args.action == "cancel":
            response = client.post(path + "/cancel")
        else:
            response = client.get(path)
        # Exclusive creation preserves prior evidence; HTTP errors remain inspectable and nonzero.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump({"status": response.status_code, "body": response.json()}, output, ensure_ascii=False, indent=2)
        response.raise_for_status()
    print(f"Saved {args.action} evidence to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
