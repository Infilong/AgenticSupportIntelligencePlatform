# Architecture decision record — M0

Status: M1 foundation in progress. API/database, vector extension migration, health and request
logging are implemented. Session/workspace APIs, frontend and worker foundation now exist;
AI processing remains. M1 browser paths passed; whole release gates remain incomplete.

## Runtime

Development: Vite frontend → FastAPI → PostgreSQL/pgvector; one Python worker reads the same
database. Local release: FastAPI serves built frontend assets, reducing this to app, worker,
database. Docker project `asi-rebuild-v1`; reserve loopback ports 5180, 8010, 5440 for development.
M1 runs API/database on 8010/5440, frontend on 5180 and a worker without a public port.

The old `asi-verification` stack is separate and remains untouched. The old Redis container
belongs to that stack; it is not part of the rebuild. New volumes must carry the new namespace.

## Decisions fixed for V1

- PostgreSQL stores messages, knowledge originals/versions/chunks, runs, review, usage and jobs.
- A pending job and its business record commit atomically; queue transport cannot lose the job.
- One worker initially; short claims with leases, heartbeats, fenced updates and bounded retries.
- Never hold a DB transaction open while waiting on a provider. Model outcomes may be uncertain
  after a crash; preserve accounting uncertainty and prevent duplicate publication.
- Supported PostgreSQL LangGraph checkpoints persist workflow state. A review pause releases
  the worker; authorized resume continues the same graph through a scheduled job.
- Server authentication, roles and workspace scoping precede reads, writes and model dispatch.
- LangChain supplies selected integration/splitting components; LangGraph coordinates the graph.
- Domain services own rules; API routes, graph nodes and worker handlers call those services.
- Maintain distinct original message, linked attempt, draft, reviewed final and decision history.
- Use exact SQL vector search and a measured bounded lexical baseline; no broad new search stack.

Refer to REBUILD_PLAN for the target repository topology; create files only when needed.

## Initial workbench design direction

```text
Workspace / provider mode                  New message   Import
Navigation     Inbox and filters           Selected message
Workbench      Needs attention / All       Original customer message
Knowledge      Search                     Response / next required action
Quality        Message + status           [1] [2] supporting sources
Settings       Message + status           Edit / approve / clarify / retry
                                          Processing details (expand)
                                          Attempt history (expand)
```

Citation selection opens a source drawer beside the response with exact version and section.
No separate response editor on a review page. On small screens, navigate list → detail → source,
with clear back navigation and focus restoration. Use a restrained neutral palette and one
accent color; status must also be expressed in text. This is a direction, not a reviewed UI.

## Questions to resolve during the owning milestone

M1 uses opaque PostgreSQL sessions with hashed random cookie tokens, Argon2 passwords,
absolute/idle expiry, synchronizer CSRF tokens and exact configured Origin validation. The
cookie name is distinct from archived apps because cookies are not isolated by port.
Membership writes lock the workspace and recheck authority/admin count inside the transaction.
The responsive React frontend implements login, workspace navigation and member roles.
OpenAPI generates its response types; release product journeys remain incomplete.
M2 specifies token/context limits, chunking parameters, source-equivalence mappings and initial
quality thresholds before tuning. M3 verifies worker lease timing and graph resume behavior.
These choices cannot weaken the release contract; material changes need approval.

## Implemented worker boundary

`jobs` owns payload-bound idempotency, priority, attempts, availability and leases. Claims use
`FOR UPDATE SKIP LOCKED`; every heartbeat/publication requires the current unexpired UUID lease.
Expired jobs are reclaimed or terminated after three attempts. Retry backoff is bounded.
Workspace authorization and publication use the same workspace-first lock order as membership
changes. Handlers execute outside transactions and cannot publish after revocation/cancellation.
The current handler performs an actual PostgreSQL/vector/schema diagnostic. It is not ingestion.

Cancellation prevents publication now; long handlers added in M2 must check cancellation and
lease ownership between bounded batches. Python threads do not preempt an executing handler.
LangGraph continuation and business-result publication remain distinct responsibilities.
