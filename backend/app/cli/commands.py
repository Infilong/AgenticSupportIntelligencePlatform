"""CLI operations delegate validation, authority and mutation to the HTTP API."""

import time
from urllib.parse import quote, urlencode
from uuid import UUID, uuid4

from app.cli.errors import CliError


def identifier(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as error:
        raise CliError("A valid UUID is required.") from error


def agent_id(client, base, value):
    try:
        return str(UUID(value))
    except ValueError:
        page = client.call(base + "/agents?" + urlencode({"search": value, "limit": 100}))
        matches = [item for item in page["items"] if item["name"].casefold() == value.casefold()]
        if len(matches) != 1 or page["has_next"]:
            raise CliError(
                "Agent name is missing or ambiguous; use its UUID from 'asi agent list'."
            ) from None
        return matches[0]["id"]


def execute(args, client, emit):
    if args.group == "workspace":
        return client.call("/workspaces")
    if not args.workspace:
        raise CliError("Choose --workspace UUID or set ASI_WORKSPACE.")
    base = "/workspaces/" + identifier(args.workspace)
    if args.group == "agent":
        if args.offset < 0:
            raise CliError("Offset cannot be negative.")
        return client.call(
            base
            + "/agents?"
            + urlencode({"search": args.search, "offset": args.offset, "limit": 20})
        )
    if args.group == "knowledge":
        if args.file.suffix.lower() not in {".txt", ".md", ".markdown"}:
            raise CliError("Use a UTF-8 text or Markdown file.")
        with args.file.open("rb") as handle:
            raw = handle.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise CliError("File exceeds the 2 MiB upload limit.")
        content = raw.decode("utf-8-sig")
        if not content.strip() or "\0" in content:
            raise CliError("File must contain nonblank UTF-8 text without NUL bytes.")
        return client.call(
            base + "/knowledge-documents",
            method="POST",
            body={
                "title": args.title or args.file.stem,
                "content": content,
                "content_type": "text/plain"
                if args.file.suffix.lower() == ".txt"
                else "text/markdown",
                "language": args.language,
            },
        )
    if args.group == "task":
        key = args.request_key or str(uuid4())
        try:
            result = client.call(
                base + "/tasks",
                method="POST",
                body={
                    "agent_id": agent_id(client, base, args.agent),
                    "input_message": args.message,
                    "request_key": key,
                },
            )
        except CliError as error:
            error.details = {"request_key": key}
            raise
        return {**result, "request_key": key}
    if args.group == "run":
        run_id = quote(identifier(args.id))
        path = base + f"/task-runs/{run_id}"
        if args.command == "stop":
            return client.call(path + "/stop", method="POST")
        if args.command == "inspect":
            task = client.call(path)
            return {
                **task,
                "trace": client.call(base + f"/agent-runs/{run_id}/trace"),
                "actions": client.call(path + "/actions?limit=100"),
                "attempts": client.call(path + "/attempts?limit=100") if task["task_id"] else None,
                "configuration": client.call(path + "/configuration") if task["task_id"] else None,
            }
        return watch(args, client, path, emit)
    if args.group == "review":
        if args.command == "list":
            if args.offset < 0:
                raise CliError("Offset cannot be negative.")
            return client.call(
                base + f"/human-reviews?decision=pending&limit=20&offset={args.offset}"
            )
        id = identifier(args.id)
        if args.action:
            if not args.expected_hash:
                raise CliError(
                    "Action approval/rejection requires --expected-hash from run inspect."
                )
            return client.call(
                base + f"/task-actions/{id}/resolve",
                method="POST",
                body={
                    "expected_hash": args.expected_hash,
                    "decision": args.command,
                    "reason": args.reason or "",
                },
            )
        return client.call(
            base + f"/human-reviews/{id}/resolve",
            method="POST",
            body={
                "decision": "approved" if args.command == "approve" else "rejected",
                "comments": args.reason,
                "edited_answer": None,
            },
        )
    raise CliError("Unsupported command.")


def watch(args, client, path, emit):
    if not 0.2 <= args.interval <= 60 or not 0 < args.timeout <= 86400:
        raise CliError("Watch interval must be 0.2–60 seconds and timeout 1–86400 seconds.")
    deadline, previous = time.monotonic() + args.timeout, None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CliError("Watch timed out; the task may still be running.", 9)
        try:
            result = client.call(path, timeout=min(30, remaining))
        except CliError as error:
            if time.monotonic() >= deadline:
                raise CliError("Watch timed out; the task may still be running.", 9) from error
            raise
        status = result["run"]["status"]
        if status != previous:
            emit(result)
            previous = status
        if status in {"completed", "needs_human_review"}:
            return None
        if status in {"failed", "rejected", "stopped"}:
            raise CliError(f"Run ended with status {status}.", 8)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CliError("Watch timed out; the task may still be running.", 9)
        time.sleep(min(args.interval, remaining))
