"""Commands implemented for M0. Application commands arrive with their milestones."""
import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor", "verify-prep", "verify-browser", "evidence"])
    parser.add_argument("--offline", action="store_true", help="Skip registry probes in doctor")
    args = parser.parse_args()
    if args.offline and args.command != "doctor":
        parser.error("--offline applies only to doctor")
    if args.command == "doctor":
        from doctor import main as doctor
        return doctor(["--offline"] if args.offline else [])
    from evidence import run_checked, summarize
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
