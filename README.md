# Agentic Support Intelligence Platform

A local-first RAG and AI agent administration app for a small team. Provide company
knowledge, ask support questions in English, Japanese or Chinese, review proposed changes,
and inspect what the agent did. The interface is inspired by Dify, with a deliberately
smaller scope: five areas, a shared backend and a practical CLI.

## Main workflow

| Area | What you do |
| --- | --- |
| Work | Ask questions, follow tasks and handle requests needing human review. |
| Knowledge | Add text or Markdown, inspect processing failures, retry and maintain documents. |
| Agents | Set instructions, model, permitted knowledge and allowed internal actions. |
| Activity | Inspect shared execution records, evidence, steps, model calls and interventions. |
| Settings | Manage workspace members, roles and model configuration. |

Start by adding knowledge and configuring an agent. Ask a question in Work, inspect its
cited evidence, and review any proposed category or internal note. Approval applies to the
exact proposed input. You can edit a draft answer, reject a request, stop a task, or create
a linked attempt with corrected instructions. Prior attempts and applied actions remain recorded.

## Permissions and human control

| Role | Capabilities |
| --- | --- |
| Viewer | Read permitted work, knowledge and activity. |
| Operator | Viewer access plus start/stop tasks and resolve reviews. |
| Admin | Operator access plus knowledge, agents and lower-role member management. |
| Owner | Full workspace administration, privileged membership and model settings. |

The API enforces workspace scope and permissions for browser, CLI and agent actions.
An agent's allowed actions are also limited by its initiating user's authority. Migration
0037 retires legacy memberships: Reviewer becomes Operator; Member and Developer become
Admin. Each authority change is audited. Back up before upgrading; use forward repair or
a verified backup restore rather than downgrade to reverse this transition.

Runs execute through a durable worker. Stop requests prevent later steps and publication;
an in-flight call may finish before Stopping becomes Stopped. Stopping does not undo
already approved changes or guarantee cancellation of provider charges. Interrupted work
is not automatically replayed. A corrected attempt has a new execution record.

## Run locally

Requirements: Docker Desktop with Compose. From the repository root:

```sh
docker compose up -d --build
```

Open [the app](http://localhost:5173). The API is at [localhost:8000](http://localhost:8000/docs)
and its [health endpoint](http://localhost:8000/health) reports availability. API startup
applies migrations; the worker waits for the API to be healthy. Create an account and
workspace, then follow Knowledge → Agents → Work.

If you already use the verification stack, keep its project name:
`docker compose -p asi-verification up -d --build`. Do not start a second stack on the same ports.
Set the `FRONTEND_PORT` environment variable before starting Compose if port 5173 is occupied.
All published service ports bind to loopback. See the [infrastructure guide](infra/README.md)
for deployment settings and the verified logical backup/restore procedure.

`/` is the main interface. `/rebuild.html` preserves saved links to it. The obsolete
interface has been removed; browser workflows use the five-area app.

## CLI

From `backend/`, run `uv sync --frozen --extra dev`, then `uv run --frozen asi --help`.
An activated installed environment exposes `asi` directly:

```text
asi auth login
asi workspace list
asi --workspace WORKSPACE_UUID knowledge add ./policy.md
asi --workspace WORKSPACE_UUID agent list
asi --workspace WORKSPACE_UUID task create --agent support --message "Explain the refund policy"
asi --workspace WORKSPACE_UUID run watch RUN_UUID
asi --workspace WORKSPACE_UUID run inspect RUN_UUID --json
asi --workspace WORKSPACE_UUID run stop RUN_UUID
asi --workspace WORKSPACE_UUID review list
asi --workspace WORKSPACE_UUID review approve REVIEW_UUID
asi --workspace WORKSPACE_UUID review reject REVIEW_UUID --reason "Insufficient evidence"
```

The [CLI guide](docs/cli.md) covers secure login, workspace selection, exact action approval,
non-interactive operation, versioned JSON and exit codes. CLI operations use the same API
permissions and records as the browser.

## Architecture and verification

React/TypeScript/Vite serves the interface. One modular FastAPI backend owns authentication,
permissions, retrieval, task admission, reviews and accounting. PostgreSQL/pgvector stores
knowledge and execution state; a worker runs the bounded LangGraph support workflow.
The Compose stack also includes Redis. See [architecture](ARCHITECTURE.md) and the
[code map](docs/code-map.md) for module ownership.

Recorded evidence includes multilingual mock journeys, permission and transaction tests,
exact-action approval and duplicate prevention, CLI acceptance, browser cancellation and
recovery of the current database schema. The [testing guide](docs/testing.md) contains
commands, dated results and their limits. The [rebuild plan](docs/exec-plans/completed/simple-admin-rebuild.md)
records delivery evidence and limits. Passing these checks does not establish production readiness.

Models and embeddings default to deterministic mocks. Configured OpenAI-compatible providers
are supported, but real-provider quality and cancellation remain separately unverified.
Credentials belong on the backend; do not put provider keys in browser inputs or source control.
Costs are estimates, not billing records. Automated multilingual regressions verify control
flow and expected facts, not general model quality. Local restore evidence does not establish
offsite disaster recovery, operational load capacity or enterprise deployment readiness.

## Agent-first development

Start with [AGENTS.md](AGENTS.md) and the [documentation router](docs/README.md). Read
[coding rules](codingRules.md) before source changes. Keep changes focused, use deterministic
providers in tests, verify UI behavior in a browser, and preserve failed evidence. Architecture,
setup, tests and CLI each have an owning guide; plans preserve decisions and unfinished work.
Historical evaluation, learning and portfolio material remains available through the router.
