"""Discoverable command surface; every workspace operation requires explicit scope."""

import argparse
import os
from pathlib import Path

from app.cli.errors import CliError


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CliError(message)


def parser():
    root = Parser(prog="asi", description="Run and supervise support tasks through the shared API.")
    root.add_argument("--api-url", default=os.environ.get("ASI_API_URL", "http://127.0.0.1:8000"))
    root.add_argument(
        "--session-file",
        type=Path,
        default=Path(os.environ.get("ASI_SESSION_FILE", Path.home() / ".asi/session.json")),
    )
    root.add_argument("--workspace", default=os.environ.get("ASI_WORKSPACE"), help="Workspace UUID")
    root.add_argument(
        "--json", action="store_true", help="Compact versioned JSON (watch: JSON lines)"
    )
    groups = root.add_subparsers(dest="group", required=True)
    auth = groups.add_parser("auth").add_subparsers(dest="command", required=True)
    login = auth.add_parser(
        "login", help="Save a local API-bound session without printing its token"
    )
    login.add_argument(
        "--email", help="Email address; prompted when omitted in an interactive terminal"
    )
    login.add_argument("--password-stdin", action="store_true")
    workspace = groups.add_parser("workspace").add_subparsers(dest="command", required=True)
    workspace.add_parser("list")
    agent = (
        groups.add_parser("agent").add_subparsers(dest="command", required=True).add_parser("list")
    )
    agent.add_argument("--search", default="")
    agent.add_argument("--offset", type=int, default=0)
    knowledge = groups.add_parser("knowledge").add_subparsers(dest="command", required=True)
    add = knowledge.add_parser("add", help="Upload UTF-8 text or Markdown, maximum 2 MiB")
    add.add_argument("file", type=Path)
    add.add_argument("--title")
    add.add_argument("--language", choices=["en", "ja", "zh"])
    task = (
        groups.add_parser("task").add_subparsers(dest="command", required=True).add_parser("create")
    )
    task.add_argument("--agent", required=True, help="Agent UUID or unique exact name")
    task.add_argument("--message", required=True)
    task.add_argument("--request-key", help="Reuse this key when retrying an unchanged submission")
    run = groups.add_parser("run").add_subparsers(dest="command", required=True)
    for name in ("inspect", "stop", "watch"):
        command = run.add_parser(name)
        command.add_argument("id")
        if name == "watch":
            command.add_argument("--interval", type=float, default=1)
            command.add_argument("--timeout", type=float, default=300)
    review = groups.add_parser("review").add_subparsers(dest="command", required=True)
    listing = review.add_parser("list")
    listing.add_argument("--offset", type=int, default=0)
    for name in ("approve", "reject"):
        command = review.add_parser(name)
        command.add_argument("id")
        command.add_argument("--action", action="store_true", help="Resolve a task action proposal")
        command.add_argument(
            "--expected-hash", help="Exact hash shown by run inspect; required for actions"
        )
        command.add_argument("--reason", required=name == "reject")
    return root


def normalize_options(argv):
    # Permit common options before or after subcommands, including `run inspect ID --json`.
    front, rest = [], []
    index = 0
    while index < len(argv):
        value = argv[index]
        if value == "--json":
            front.append(value)
        elif value in {"--api-url", "--session-file", "--workspace"}:
            if index + 1 >= len(argv):
                raise CliError(f"{value} requires a value.")
            front.extend(argv[index : index + 2])
            index += 1
        elif any(
            value.startswith(name + "=") for name in ("--api-url", "--session-file", "--workspace")
        ):
            front.append(value)
        else:
            rest.append(value)
        index += 1
    return front + rest
