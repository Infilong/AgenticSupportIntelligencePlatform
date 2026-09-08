# Architecture decision record — M0

Status: M1 foundation in progress. API/database, vector extension migration, health and request
logging are implemented. Auth, frontend, worker and AI processing remain to implement.

## Runtime

Development: Vite frontend → FastAPI → PostgreSQL/pgvector; one Python worker reads the same
database. Local release: FastAPI serves built frontend assets, reducing this to app, worker,
database. Docker project `asi-rebuild-v1`; reserve loopback ports 5180, 8010, 5440 for development.
M1 currently runs the isolated API/database on 8010/5440. Frontend/worker follow in later slices.

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

M1 chooses compatible pinned backend/frontend dependencies, secure sessions and CSRF handling.
M2 specifies token/context limits, chunking parameters, source-equivalence mappings and initial
quality thresholds before tuning. M3 verifies worker lease timing and graph resume behavior.
These choices cannot weaken the release contract; material changes need approval.
