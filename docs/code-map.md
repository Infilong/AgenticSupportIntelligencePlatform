# Current code map

Reviewed against the working tree on 2026-09-08. This file describes implementation;
[architecture](../ARCHITECTURE.md) defines top-level contracts. Update this map when ownership changes.

## Entry points and boundaries

| Area | Entry point / owner | Local guide |
| --- | --- | --- |
| Browser | `frontend/src/rebuild/main.tsx` → `WorkspaceApp.tsx` → feature modules | [Frontend](../frontend/README.md) |
| HTTP API | `backend/app/main.py` → `api/v1/router.py` → domain routers | [Backend](../backend/README.md) |
| Authentication / authorization | `dependencies/auth.py`, `dependencies/workspace.py`, `services/workspace_service.py` | [API boundary](../backend/app/api/README.md) |
| Business workflows | `backend/app/services/` | [Service ownership](../backend/app/services/README.md) |
| Database | `app/models/`, `app/db/session.py`, `alembic/versions/` | [Migrations](../backend/alembic/README.md) |
| Validation | `backend/tests/`, `frontend/tests/e2e/`, `scripts/tests/` | [Testing](testing.md) |
| Runtime | root Compose file and component Dockerfiles | [Infrastructure](../infra/README.md) |
| Repository tooling | `scripts/` and `.github/workflows/ci.yml` | [Scripts](../scripts/README.md) |

## Request and data flow

```text
Browser feature → typed API client → apiRequest → FastAPI router
  → authenticated user + workspace permission dependency
  → Pydantic input → domain service → SQLAlchemy models/session
  → response schema → feature state → rendering

Agent run → AgentService → SupportAgentGraphRunner
  → language → classification → retrieval → context packing → draft
  → confidence → route → finalize or human review
  → persisted graph steps, checkpoints, tool calls, AI runs and guardrails
```

## Current coupling and gaps

- `frontend/src/rebuild/WorkspaceApp.tsx` owns session/workspace identity and navigation;
  workspace-keyed content discards scoped drafts and rejects stale read results. Feature
  modules own Work/Knowledge/Agents/Activity/Settings; Work and Activity share RunDetail.
- `app/apiRequest.ts` owns HTTP transport and status-bearing errors; the root binds authenticated
  401 failures to the current scope. Background read failures remain visible and manually retryable.
- `backend/app/core/request_logging.py` owns HTTP outcome records; `request_context.py` carries
  their ID to `workflow_logging.py` for persisted graph creation events. `error_responses.py`
  owns generic unexpected-error responses. The browser HTTP client validates and displays
  5xx references; [observability](observability-design.md) owns the exact contract and limits.
- `backend/app/logging.json` configures Uvicorn's `core/server_logging.py` formatter for
  exception diagnostics without exception/source text. The backend Dockerfile loads it and
  disables duplicate access logs; this is a server-specific boundary, not global redaction.
- `rebuild/work/Work.tsx` owns request composition and language selection; `work/api.ts`
  sends durable task requests. `task_admission.py` checks permissions and persists execution;
  `app/worker.py` executes bounded work with PostgreSQL ownership locks. Task actions,
  linked attempts and stop use shared backend contracts for browser and CLI.
- Backend services perform SQLAlchemy queries and commits directly. Some routers also query
  models. A repository layer is an incremental destination, not an implemented boundary.
- Graph checkpoints are snapshots, not arbitrary resume points. Queued tasks are durable;
  interrupted active work fails explicitly and can start a linked attempt after review.
- Redis runs in Compose, but there is no worker queue implementation.
- Embeddings default to deterministic mocks; `embedding_runtime.py` selects opt-in accounted
  OpenAI embeddings. `knowledge_indexing.py` owns chunk/index persistence and
  `knowledge_contracts.py` owns domain results/errors; the knowledge service owns management.
  `graph_retrieval.py` owns retrieval node execution, failure routing and embedding-step linkage.
  `embedding_reconciliation.py` owns audited operator usage confirmation;
  `embedding_recovery.py` owns the separate pending-to-uncertain orphan transition using
  `execution_ownership.py` PostgreSQL session locks. These backend operations remain available; the old Costs panel has been retired. Recovery retains estimated usage and rejects live or legacy unowned
  attempts; it does not retry provider calls or confirm billing. Model-call recovery and real
  semantic quality remain open; see the [recovery plan](exec-plans/active/interrupted-call-recovery.md).
- Evaluation baselines use the configured provider and bounded RAG context; current metrics
  report citation presence. Factual support grading and real-provider quality evidence remain
  missing; citation presence is not proof that an answer is supported.

## Refactoring order

1. Preserve behavior with focused tests and a passing browser path.
2. Keep feature API operations behind `apiRequest.ts`; preserve response contracts and
   session-rejection handling.
3. Move one feature's state/orchestration into its hook, leaving rendering in its page.
4. Split graph node execution, persistence and workflow summaries by responsibility.
5. Extract repeated persistence operations where transactions or reuse justify it.

New boundaries must name their owner and allowed dependencies. UI cannot own authorization,
database schema or token accounting. Schemas/models must not depend on routers or UI.
Avoid moving files only to make the directory tree look cleaner.

## Evidence and work queue

See [testing](testing.md), [production audit](audits/production-readiness-2026-09-07.md)
and the [automatic improvement loop](production-improvement-loop.md). Historical ticket
completion notes are not evidence of current runtime behavior.
