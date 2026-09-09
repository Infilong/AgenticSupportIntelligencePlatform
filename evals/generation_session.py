"""Reuse a server-validated local session without repeated password authentication."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def authenticate(client, credentials, session_path):
    if session_path is not None:
        session_path = session_path.resolve()
        if not session_path.is_relative_to((ROOT / ".artifacts").resolve()):
            raise ValueError("Session files must stay under the ignored repository .artifacts directory")
        if session_path.exists():
            stored = json.loads(session_path.read_text(encoding="utf-8"))
            for name, value in stored.items():
                client.cookies.set(name, value, domain="127.0.0.1", path="/")
    response = client.get("/api/session")
    response.raise_for_status()
    current = response.json()
    client.headers.update({"Origin": "http://127.0.0.1:5180", "X-CSRF-Token": current["csrf_token"]})
    user = current.get("user")
    if user and user["email"].casefold() != credentials["accounts"]["admin"].casefold():
        raise ValueError("Saved session belongs to another account")
    if not user:
        response = client.post("/api/session/login", json={"email": credentials["accounts"]["admin"],
                                                          "password": credentials["password"]})
        response.raise_for_status()
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    if session_path is not None:
        session_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(session_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(dict(client.cookies), output)
