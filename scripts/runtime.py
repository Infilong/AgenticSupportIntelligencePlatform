"""Commands for the isolated rebuild only; never target archived Compose projects."""
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def init_env():
    path = ROOT / ".env"
    try:
        with path.open("x", encoding="utf-8") as output:
            output.write("# Local rebuild only. Never commit.\n")
            output.write(f"ASI_DATABASE_PASSWORD={secrets.token_urlsafe(32)}\n")
            output.write("ASI_DATABASE_PORT=5440\nASI_API_PORT=8010\nASI_WEB_PORT=5180\n")
    except FileExistsError:
        print("Existing .env preserved; no values were read or printed.")
    else:
        print("Created ignored .env with a generated database credential.")
    return 0


def compose(*arguments):
    if not (ROOT / ".env").is_file():
        print("Missing .env. Run python scripts/manage.py init-env first.")
        return 1
    command = ["docker", "compose", "--project-directory", str(ROOT), "--env-file", str(ROOT / ".env"),
               "-f", str(ROOT / "compose.yaml"), "-p", "asi-rebuild-v1", *arguments]
    return subprocess.run(command, cwd=ROOT, timeout=600).returncode


def execute(command):
    if command == "init-env":
        return init_env()
    if command == "up":
        for args in [("up", "-d", "--wait", "postgres"),
                     ("build", "api"),
                     ("run", "--rm", "api", "uv", "run", "--frozen", "alembic", "upgrade", "head"),
                     ("up", "-d", "--wait", "api")]:
            code = compose(*args)
            if code:
                return code
        return 0
    if command == "migrate":
        return compose("run", "--rm", "api", "uv", "run", "--frozen", "alembic", "upgrade", "head")
    if command == "down":
        return compose("down")  # No volume removal; only the fixed rebuild project.
    raise ValueError("Unknown runtime command")
