"""Verified preparation and incremental application commands."""
import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor", "verify-prep", "verify-browser", "evidence",
                                            "init-env", "up", "migrate", "down", "verify-backend",
                                            "verify-integration", "verify-inbox-capacity", "seed-demo", "verify-worker", "prepare-model",
                                            "verify-ingestion"])
    parser.add_argument("--offline", action="store_true", help="Skip registry probes in doctor")
    args = parser.parse_args()
    if args.offline and args.command != "doctor":
        parser.error("--offline applies only to doctor")
    if args.command == "doctor":
        from doctor import main as doctor
        return doctor(["--offline"] if args.offline else [])
    if args.command in {"init-env", "up", "migrate", "down"}:
        from runtime import execute
        return execute(args.command)
    if args.command == "seed-demo":
        from seed_demo import main as seed
        return seed()
    from evidence import run_checked, summarize
    if args.command == "verify-ingestion":
        return run_checked("ingestion", [shutil.which("uv") or "uv", "run", "--frozen", "python",
                           "-m", "app.ingestion_probe"], ROOT / "backend")
    if args.command in {"verify-worker", "prepare-model"}:
        module = "app.worker_probe" if args.command == "verify-worker" else "app.providers.prepare_model"
        return run_checked(args.command, ["docker", "compose", "--project-directory", str(ROOT),
                           "--env-file", str(ROOT / ".env"), "-f", str(ROOT / "compose.yaml"),
                           "-p", "asi-rebuild-v1", "run", "--rm", "api", "uv", "run",
                           "--frozen", "python", "-m", module], ROOT,
                           timeout=600 if args.command == "prepare-model" else 180)
    if args.command in {"verify-integration", "verify-inbox-capacity"}:
        from verify_integration import main as integration
        return integration(capacity=args.command == "verify-inbox-capacity")
    if args.command == "verify-backend":
        uv = shutil.which("uv")
        if not uv:
            print("uv is required for backend checks.", file=sys.stderr)
            return 1
        return run_checked("backend", [uv, "run", "--frozen", "pytest", "-q"], ROOT / "backend")
    if args.command == "evidence":
        return summarize()
    if args.command == "verify-prep":
        return run_checked("prep", [sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"], ROOT)
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        print("npm is unavailable. Install Node.js before browser verification.", file=sys.stderr)
        return 1
    env = {**os.environ, "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / ".artifacts" / "browsers")}
    return run_checked("browser", [npm, "run", "test:environment"], ROOT / "frontend", env)


if __name__ == "__main__":
    raise SystemExit(main())
