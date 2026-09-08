"""Keep generated development login credentials private and stable across repeated seeding."""
import json
import os
import secrets
import subprocess

from runtime import ROOT


def main():
    path = ROOT / ".artifacts/m1/demo-credentials.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"password": secrets.token_urlsafe(24), "accounts": {
            role: f"{role}@asterworks.example" for role in ("admin", "operator", "viewer", "private")}}
        with path.open("x", encoding="utf-8") as output:
            json.dump(data, output, indent=2)
    command = ["docker", "compose", "--project-directory", str(ROOT), "--env-file", str(ROOT / ".env"),
               "-f", str(ROOT / "compose.yaml"), "-p", "asi-rebuild-v1", "run", "--rm", "-e",
               "ASI_DEMO_PASSWORD", "api", "uv", "run", "--frozen", "python", "-m", "app.bootstrap"]
    result = subprocess.run(command, cwd=ROOT, env={**os.environ, "ASI_DEMO_PASSWORD": data["password"]}, timeout=90)
    if result.returncode == 0:
        print(f"Development login credentials are in the ignored file: {path}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
