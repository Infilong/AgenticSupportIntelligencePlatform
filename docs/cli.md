# CLI guide

`asi` is a thin client of the same `/api/v1` endpoints used by the browser. It does not
run agents locally or bypass workspace permissions, review, accounting or stop controls.
Its implementation lives in [app/cli](../backend/app/cli/). Python 3.12 is required by the
backend package; the CLI itself uses only the standard library.

## Start

From `backend/`, install the existing locked backend environment with
`uv sync --frozen --extra dev`, then use `uv run --frozen asi --help`.
An activated installed environment exposes `asi` directly. Without installing the backend,
`python -m app.cli --help` from `backend/` invokes the same client using the standard library.

```text
asi auth login
asi workspace list
asi --workspace WORKSPACE_UUID agent list
asi --workspace WORKSPACE_UUID knowledge add ./policy.md --language en
asi --workspace WORKSPACE_UUID task create --agent support --message "Explain the refund policy"
asi --workspace WORKSPACE_UUID run watch RUN_UUID
asi --workspace WORKSPACE_UUID run inspect RUN_UUID --json
asi --workspace WORKSPACE_UUID run stop RUN_UUID
asi --workspace WORKSPACE_UUID review list
asi --workspace WORKSPACE_UUID review approve REVIEW_UUID
asi --workspace WORKSPACE_UUID review reject REVIEW_UUID --reason "Insufficient evidence"
```

Workspace selection is always explicit: `--workspace` or `ASI_WORKSPACE`. The default API
is `http://127.0.0.1:8000`; set `--api-url` or `ASI_API_URL` for another server. Remote
servers require HTTPS. Common options may appear before or after the subcommand.
Agent names must match a unique exact name; use the UUID when ambiguous. Lists are bounded;
agent and review lists accept `--offset`, and agent lists also accept `--search`.

Uploads accept UTF-8 `.txt`, `.md` or `.markdown` files up to 2 MiB, with optional `--title`
and `--language en|ja|zh`. Processing results come from the backend.

## Credentials and automation

Interactive login prompts for email and a hidden password. For automation, use
`auth login --email EMAIL --password-stdin` with a UTF-8 password supplied by a secret
manager through stdin. Do not place passwords in command arguments or shell history.
Login never prints the access token. Alternatively supply an existing token via `ASI_TOKEN`.

Sessions default to `~/.asi/session.json`; override with `--session-file` or
`ASI_SESSION_FILE`. Tokens use Windows DPAPI, or an owner-only file on POSIX. A saved
session only works with its original API address. Sign in again when it expires. HTTP
redirects are rejected rather than forwarding credentials to a new address.

`--json` emits UTF-8 JSON with `schema_version: 1`, `ok`, and `data`; failures use `error`
on stderr. Watch emits one JSON line per status change. Human-readable mode pretty-prints
the same result. `run inspect` includes the API execution trace, proposals and a bounded
attempt-history page. Treat identifiers and recorded statuses as authoritative.

Task creation returns its `request_key`; connection errors also preserve that key in the
error details. Retry the unchanged command with `--request-key KEY`. The CLI does not
automatically replay writes. Watch accepts `--interval` (0.2–60 seconds) and `--timeout`
(up to one day); it exits at completion or human review and never automatically approves.
Interrupting/timing out a watch does not stop server work; use `run stop` explicitly.

Action proposals are distinct from answer reviews. Inspect the exact action and inputs,
then pass its ID and hash:

```text
asi --workspace WORKSPACE_UUID review approve PROPOSAL_UUID --action --expected-hash HASH
asi --workspace WORKSPACE_UUID review reject PROPOSAL_UUID --action --expected-hash HASH --reason "Not appropriate"
```

Changed inputs require a new approval. Answer approval is blocked while actions remain
pending. Rejection and stopping do not reverse an already applied update or provider charge.

| Exit | Meaning |
| --- | --- |
| 0 | Command succeeded; watch may be awaiting human review |
| 2 | Invalid arguments/input or rejected API request |
| 3 | Missing, expired or unusable authentication |
| 4 | Permission denied |
| 5 | Resource not found |
| 6 | Conflict, including stale action hash or changed request key |
| 7 | Transport/server/response failure |
| 8 | Watched run ended failed, rejected or stopped |
| 9 | Watch timed out |
| 130 | Interrupted locally |

The [testing guide](testing.md) records mock-provider acceptance. Real-provider quality
and billing correctness require separate verification.

`run inspect` also includes `configuration` for durable tasks: the saved agent name,
instructions, model assignment, budget, knowledge scope and allowed actions. This is a
redacted whitelist of the admission snapshot, not the agent's current editable settings.
Legacy runs without durable task metadata return null for configuration.
