# Architecture and current topology

Updated 2026-09-09 for workflow inspection and full-width inbox navigation built on `00bfe7e`.
Foundation, knowledge ingestion, real retrieval and the message-to-development-draft API exist.
The workbench UI and human-review continuation are connected. [STATUS](STATUS.md) owns verification.

## Current project topology

```text
AgenticSupportIntelligencePlatform/
├── AGENTS.md                   # Task routing and authority
├── REBUILD_PLAN.md             # Release requirements and target structure
├── compose.yaml               # Four-service development runtime
├── backend/
│   ├── migrations/versions/    # Application schema
│   ├── app/
│   │   ├── main.py             # FastAPI composition
│   │   ├── worker.py           # Job polling and handlers
│   │   ├── core/              # Settings, health, logging, body limits
│   │   ├── db/                # Engine, sessions and model base
│   │   ├── jobs/              # Claims, leases, cancellation and fencing
│   │   ├── modules/
│   │   │   ├── identity/      # Sessions, authentication and CSRF
│   │   │   ├── workspaces/    # Membership and roles
│   │   │   ├── knowledge/     # Documents, ingestion, retrieval and sources
│   │   │   ├── support/       # Original messages, runs, handoffs and cited drafts
│   │   │   ├── reviews/       # Attributable decisions and fenced final responses
│   │   │   └── usage/         # Model-call records
│   │   ├── providers/         # Local embeddings/reranker and recorded calls
│   │   └── workflows/         # LangGraph orchestration and PostgreSQL checkpoints
│   └── tests/                 # Unit and PostgreSQL integration tests
├── frontend/
│   ├── src/app/               # Shell and routing
│   ├── src/api/               # Client and generated API types
│   ├── src/features/auth/     # Login and session state
│   ├── src/features/settings/ # Workspace members
│   ├── src/features/workbench/ # Inbox, run details, citations, development and review
│   ├── src/features/knowledge/ # Upload, search and source inspection
│   └── tests/e2e/             # Browser journeys
├── evals/                     # Frozen multilingual corpus and retrieval evaluation
├── scripts/                   # Runtime, seeding, checks and evidence
├── infra/                     # Infrastructure guidance; Compose is at root
├── docs/plans/active/          # M1 history, M2 gaps and M3 execution record
└── .github/workflows/         # Verification CI
```

Each substantive area has a local `AGENTS.md`, linked from the root director. These paths
exist now. The [target topology](../REBUILD_PLAN.md#target-project-topology) includes future
modules: separate retrieval, conversations and quality features are not
implemented. Support currently owns original messages and their processing runs; retrieval
remains in knowledge. Do not create empty target directories.

## Implemented knowledge data flow

```mermaid
flowchart LR
    Admin[Authorized admin] --> Upload[TXT or Markdown upload]
    Upload --> DB[(PostgreSQL originals, versions and jobs)]
    DB --> Worker[Worker: split and embed]
    Worker --> Vectors[(Active chunks and pgvector)]
    Member[Workspace member] --> Query[Authorize and embed query]
    Query --> Vectors
    Vectors --> Rank[Top 20 cosine candidates and local reranker]
    Rank --> Recheck[Recheck membership and active versions]
    Recheck --> Sources[Ranked passages and exact source links]
    Worker --> Records[(Model records and retrieval traces)]
    Rank --> Records
```

LangChain splitting preserves sections and normalized offsets. Pinned local multilingual
embeddings and a cross-encoder provide real retrieval without an external API. Returned
passages are candidates, not generated answers. Model records include identity, local token
counts, duration and zero external cost. Crash-abandoned synchronous records need reconciliation.

## Runtime

Development: Vite frontend → FastAPI → PostgreSQL/pgvector; one Python worker reads the same
database. Planned local release: FastAPI serves built frontend assets, reducing this to app, worker,
database. Docker project `asi-rebuild-v1`; reserve loopback ports 5180, 8010, 5440 for development.
Development config uses API/database on 8010/5440, frontend on 5180 and a worker without a public
port. This describes configuration, not current service health.

The old `asi-verification` stack is separate and remains untouched. The old Redis container
belongs to that stack; it is not part of the rebuild. New volumes must carry the new namespace.

## V1 design requirements (including unfinished application behavior)

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

Current retrieval uses vector candidates plus neural reranking. Independent BM25 and fusion
remain unimplemented requirements; the measured reranker evidence does not prove their completion.
[RAG design and audit](RAG.md) owns stage contracts, failure taxonomy and measured hardening gaps.
Application messages/runs, graph integration and human-review records now exist.

Refer to REBUILD_PLAN for the target repository topology; create files only when needed.

## Workbench navigation

```text
Workbench: searchable full-width message table → selected message
                                            ├── Response: result and permitted actions
                                            ├── Workflow: recorded stages and model evidence
                                            ├── Sources: exact cited passages and document versions
                                            └── History: decisions and linked processing attempts
```

Search, latest-attempt view, page and page size survive detail/back navigation in the URL.
The table requests 20 or 50 rows and unmounts while a message is open, avoiding hidden polling.
Tabs preserve mounted response controls while inspecting evidence. Source close restores the
originating tab and opener focus. Cancellation remains available above every tab when permitted.
Use a restrained palette and text status; the workflow is an inspector, not a graph editor.

## Foundation decisions and remaining workflow

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
The worker registers database diagnostics, document indexing, support processing and review. Indexing checks
between bounded split/embedding operations and activates versions only after fenced publication.
Failed replacements preserve the previous active version.

Cancellation and lease checks occur between bounded ingestion batches; Python threads do not
preempt an executing handler.
LangGraph continuation and business-result publication remain distinct responsibilities.

## Implemented support backend

Original message → atomic run/job → LangGraph input check → real retrieval → durable development
handoff → authenticated response submission → validated cited draft. A one-character input such
as `w` requests clarification; an empty retrieval produces insufficient evidence. Neither is
automatically routed to administrator review. Development waiting releases the worker.

The [support guide](../backend/app/modules/support/AGENTS.md) owns local invariants. The graph
uses server-derived workspace/run threads and a dedicated PostgreSQL advisory lock. Every
processing/publication boundary checks the live job lease and original requester's authority;
resume also checks the contributor. Every packed source is revalidated before export, submission
and publication, including uncited passages. Context is capped at five passages and 24,000 UTF-8
JSON bytes. This byte bound does not establish the release's complete token-budget policy.

Cancelled runs cannot resume. Duplicate submissions are idempotent; conflicting submissions fail.
Checkpoint and domain commits remain separate: replay reuses saved output and one handoff.
Graph steps expose elapsed time/errors and interrupted prior attempts; retrieval records attach
before inference so failed runs retain model-call evidence. Raw checkpoints are never public.

Real PostgreSQL tests cover authorization, cancellation, concurrent submissions and simulated
lease loss between checkpoint and publication. EN/JA/ZH API/worker smokes use actual local
models and explicitly attributed Codex-assisted drafts. These are not process-kill recovery,
external API generation, semantic answer-quality or human-review evidence.

## Connected workbench

The full-width table lists message previews, latest state/outcome, language and received time.
All/Needs attention/Ready responses/Processing/Failed filters apply to each message's latest
attempt. Counts and rows share server-side search/workspace/view semantics. Attention includes
development handoffs, human review and completed clarification/missing-evidence outcomes; Ready
contains only completed approved responses. Cancelled/rejected attempts remain in All. Pagination
supports first/previous/next/last, direct page entry and 20/50-row sizes. Shrinking results clamp
to a valid page. These views do not implement imports, labels or prove 50,000-message capacity.
At narrow widths only the table scrolls horizontally; the page remains within the viewport.

The Workflow tab renders the four recorded LangGraph stages: input check, retrieval/context,
development handoff and human review. Human review is a separate durable continuation. Missing
records are pending/not reached, with skipped labels only for known terminal branches. Terminal
orphaned starts and waiting records remain explicit instead of looking actively running. Node
completion is separate from final publication. LangChain embedding and local reranking calls are
nested within retrieval; their time must not be added again to retrieval duration. Handoff
turnaround includes waiting and is not model inference latency. Raw checkpoints stay private.
Sources retain exact saved quotes and link to the original document version; current source
activity is checked in the document view. Technical IDs remain in optional details.

Operators/admins enter messages and cancel active runs; viewers inspect records. The admin-only
development section loads authorized handoff evidence and submits a draft with an exact quote.
It is separate from human approval. Typed public projections
generate frontend contracts without exposing checkpoints.

Resource reads are keyed to route/workspace and aborted on navigation. Transient polling failures
preserve an unfinished answer; authorization failures clear protected data. Late message POST
responses cannot navigate back after leaving the screen. Aborting a request does not undo its
server write; retries of unchanged input reuse the same idempotency key within the form.
Run-state changes refresh the inbox. Imports and labels remain unfinished.

## Linked processing attempts

One message retains its original text and a maximum of ten sequenced attempts. Operator/admin
retry or added details creates a new run, job, graph, retrieval and review identity. Retry keeps
the previous input; clarification appends details within the combined 1,000-character boundary.
Overflow is rejected without truncation. Validation uses the latest actual customer input at or
before that attempt, excluding application labels and later details. Local model token limits apply.

Only the latest non-running attempt can create a child. Retry requires failure, cancellation,
rejection or insufficient evidence; added details can supersede a paused unreviewed draft by
cancelling it atomically. Original drafts, sources and decisions remain in history. Actor-bound
idempotency and locked creation prevent duplicate children; database constraints enforce scoped
lineage and sequence uniqueness. Processing checks both original requester and child creator.

The inbox shows one latest attempt per message. Optional history links expose earlier attempts;
viewers can inspect them but cannot start processing. A new child never inherits prior approval.

## Governed human review

Runs keep execution state separate from outcome. A cited draft enters `awaiting_review`;
approve/edit/reject stores an immutable actor/reason decision bound to the draft hash and revision.
The original draft and citations remain unchanged; the approved response is stored separately.
Operators/admins review ordinary drafts. Approval/edit of policy exceptions or unclassified legacy
drafts requires admin; rejection remains available to operators. Development routing annotations
are attributed inputs, not proof of semantic policy detection.

Operators/admins can also request clarification, including for policy exceptions or stale evidence,
without approving a response. The required question lives in the immutable review decision.
Fenced continuation publishes `clarification_needed` with no approved response and preserves the
original draft/citations. A queued, failed or cancelled decision remains history; its question is
not shown as an active next step. Customer replies use a fresh linked attempt and never inherit
the administrator's question as customer input. The question is recorded internally, not sent.

A separate `review-v1:{workspace}:{run}` LangGraph thread preserves completed generation history.
New drafts initialize a durable interrupt; migrated drafts initialize it when reviewed. The decision
and resume job commit atomically. Final publication rechecks the live lease, cancellation, original
requester, contributor, reviewer and exact decision; approve/edit also recheck all contextual sources.
Reject/clarify publish no approved answer and can address withdrawn evidence. Concurrency permits
only one decision and continuation.
Pending task errors/interrupts are checked even when LangGraph reports an empty `next` list.

Handoff timestamps remain raw evidence. Reversed timestamps produce `clock_anomaly` and no elapsed
value, never a fabricated zero. This flags inconsistent timing; it does not diagnose or fix clocks.

## Retrieval ownership and recovery

Each retrieval owns a dedicated PostgreSQL session advisory lock before its trace is inserted.
Inference runs without an open database transaction. Model accounting and result publication
check that session and lock the still-started trace before writing; lost ownership cannot be
reacquired by an old execution. Accounting checks are separate from user permission checks.

The worker scans bounded batches with a rotating UUID cursor. It uses nonblocking advisory and
row locks to mark abandoned started traces and their still-started calls `uncertain`, preserving
completed accounting and unknown tokens/duration/cost. No age threshold or wall-clock inference
decides abandonment. A lost database session does not prove CPU work stopped; write fencing
prevents late success/failure from replacing uncertainty. API search returns a safe retryable 503.

Deployment must replace all older API/worker instances before enabling the sweep because they
do not participate in ownership. Connection/statement/TCP settings aid detection; they do not
establish a platform-independent network deadline. Ingestion retains job-lease accounting;
this recovery boundary covers synchronous retrieval and its embedding/reranking records.
