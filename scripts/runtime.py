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
    if command in {"up", "migrate"}:
        steps = [("up", "-d", "--wait", "postgres"),
                 ("build", "api", "frontend") if command == "up" else ("build", "api"),
                 # Wait for old writers to finish before backfilling derived metadata.
                 ("stop", "--timeout", "30", "api", "worker"),
                 ("run", "--rm", "--no-deps", "api", "uv", "run", "--frozen", "alembic", "upgrade", "head")]
        if command == "up":
            steps.extend([
                ("run", "--rm", "--no-deps", "api", "uv", "run", "--frozen", "python", "-m", "app.workflows.checkpoints"),
                ("up", "-d", "--wait", "api", "frontend", "worker"),
            ])
        for args in steps:
            code = compose(*args)
            if code:
                return code
        if command == "migrate":
            print("Migrations completed; API and worker remain stopped. Run up to start the current images.")
        return 0
    if command == "down":
        return compose("down")  # No volume removal; only the fixed rebuild project.
    raise ValueError("Unknown runtime command")
