# Multilingual Support Workbench — local V1 rebuild plan

Status: full M1–M6 execution authorized on 2026-09-08. Follow STATUS for current progress;
authorization and this plan are not readiness claims.

This plan replaces the previous rebuild plan. Build a small, user-friendly RAG application
using LangChain, LangGraph and PostgreSQL. No Redis, RQ, cloud platform or large-data stack.
The previous implementation goal is retired. This contract governs the fresh rebuild;
the active goal now covers M1–M6 with verified commits and working-branch pushes.

## 1. Product purpose

Help an internal support operator produce a defensible response faster.

The main flow is:

Customer message → save original → retrieve trusted knowledge → draft a response →
inspect supporting evidence → automatic supported answer or authorized intervention.

User clarification on 2026-09-10: routine supported answers need no human approval; policy
exceptions require review, missing support requires intervention, and irrelevant/spam/meaningless
messages are retained but set aside. Automatic answers are internal machine results, never
fabricated human approvals or evidence that an external action was executed. Complete M5/M6
after this routing repair; the earlier demo-only pause is superseded.

Keep the original input, execution attempts, intermediate evidence, proposed response,
final response and human decisions linked. An operator should understand what happened
without reading JSON or learning the underlying frameworks.

English, Japanese and Chinese are first-class input, evidence and response languages.
Local-first means the application and database run locally. Authorized local inference is real
model execution without paid API access. Any future external provider sends selected content
outside the local runtime and requires separate access/spending authority; explain this in setup.

## 2. Fixed V1 scope

Include:

- Authentication, workspace membership and server-enforced permissions.
- Manual customer-message entry and bounded JSONL conversation import with labels.
- Text/Markdown knowledge uploads, originals, versions and background indexing.
- Real embeddings and PostgreSQL vector retrieval; a bounded multilingual BM25 path.
- Same-language responses with citations to exact document versions and passages.
- One configurable support workflow using LangChain and LangGraph.
- Human clarification, approve/edit/reject, cancellation and linked retries.
- Inspectable execution steps, errors, model identity, tokens, latency and estimated cost.
- Small evaluation suite comparing direct generation, vector RAG and governed hybrid RAG.
- Reproducible local startup, real browser acceptance and verified database restoration.

Explicitly defer:

- Redis, RQ, Celery, message brokers and distributed queue infrastructure.
- Kubernetes, Terraform, microservices, cloud deployment and hosted observability services.
- External vector databases, Elasticsearch, data warehouses and distributed processing.
- PDF, DOC, DOCX, OCR and multimodal ingestion. Clearly reject unsupported formats.
- Enterprise SSO, custom role designers and document-specific permission hierarchies.
- External email/refund actions, arbitrary browsing, shell tools or plugins.
- Multi-agent teams inside the product, workflow canvases and general-purpose assistants.
- An additional admin chatbot. Ordinary inspection and action controls come first.
- Model training, local-GPU deployment, advanced reranking and caching without measured need.

Do not turn imported customer conversations into trusted knowledge automatically.
V1 approval records an internal decision; it does not send a response to the customer.

## 3. User experience

Use four navigation areas. Implement the first two before Quality.

| Area | Contents |
| --- | --- |
| Workbench | Message inbox, imports, labels, drafts, review filter and per-message history |
| Knowledge | Upload, indexing status, versions, source preview and retrieval test |
| Quality | Evaluation cases/results and aggregate usage |
| Settings | Members, processing defaults and provider readiness |

The Workbench is the landing page. Show a compact searchable message list and the selected
message. Filters include needs attention, ready, processing and failed. Review is a filter
of the same inbox, not another page with a duplicate response editor.

For a selected message, show:

1. Original message and relevant customer context.
2. Response/outcome and the next meaningful action.
3. Numbered citations that open the exact supporting excerpt beside the response.
4. Expandable processing details: timeline, evidence, model calls, errors and usage.
5. Attempt history and attributable human decisions.

Keep technical IDs, raw payloads and configuration hashes in optional details.
Use readable source titles and section references. Never use chunk UUIDs as citation labels.
Tables render structured data; paragraphs render text; empty values get useful explanations.

Quality requirements:

- Consistent spacing, typography, buttons, form feedback and status colors.
- Keyboard navigation, visible focus, semantic labels and adequate contrast.
- No overlapping controls or horizontal page overflow at 360, 768 and 1440px or 200% zoom.
- Small screens switch between list and detail instead of squeezing both columns.
- Loading, empty, permission-denied, failed and retry states exist for every main flow.
- Pending forms prevent duplicate submissions and preserve input after recoverable errors.
- Workspace switching cancels/discards stale requests; refresh retains a valid workspace.
- Show provider mode clearly. Offline simulation must never look like verified live AI.
- Avoid repeated warning banners, decorative dashboards and unexplained confidence percentages.

## 4. Outcomes and permissions

Execution state and response outcome are separate fields.

Execution states: queued, running, waiting_for_input, awaiting_review, completed, failed,
cancel_requested, cancelled, rejected.

Response outcomes: grounded_draft, clarification_needed, insufficient_evidence,
conflicting_evidence, policy_review_required, approved_response, rejected_response, answered, set_aside.

| Situation | Expected experience |
| --- | --- |
| Supported routine question | Automatic internal answer with citations; inspect/copy without fabricated human approval |
| Meaningless/spam/unrelated message | Retain and set aside; allow a fresh attempt with a meaningful question |
| Relevant but ambiguous message | Request the missing details through intervention |
| Missing policy | Insufficient-evidence intervention; clarify, reject or add knowledge and retry; no unsupported approval |
| Conflicting active evidence | Show conflicting excerpts and require review |
| Policy exception | Explain the exception and required review |
| Provider failure | Technical failure with a safe retry action; no invented answer |

Use three workspace roles:

| Permission | Viewer | Operator | Admin |
| --- | --- | --- | --- |
| Read workspace messages, knowledge and traces | Yes | Yes | Yes |
| Enter/import/label messages and run processing | No | Yes | Yes |
| Clarify, cancel, retry and resolve ordinary review | No | Yes | Yes |
| Approve a policy exception | No | No | Yes |
| Upload, replace or withdraw knowledge | No | No | Yes |
| Change members and processing configuration | No | No | Yes |
| Run paid evaluation | No | No | Yes, within authorized budget |

Prevent removal/demotion of the last admin. Enforce every permission in the backend.
Treat this as a workspace-level access model: roles do not hide individual documents within
a workspace. Separate workspaces when data must be separated.

## 5. Small runtime architecture

Development uses four Compose services:

Browser → React frontend → FastAPI → PostgreSQL + pgvector
                                      ↑
                                Python worker

- Frontend: React, TypeScript, Vite, React Router and a small accessible component set.
- Backend: FastAPI, Pydantic, SQLAlchemy and Alembic; one modular application.
- Database: PostgreSQL with pgvector for business data, embeddings, jobs and checkpoints.
- Worker: one process from the same backend image, initially executing one job at a time.
- Providers: maintained OpenAI/LangChain integrations and explicit deterministic test providers.
- Tests: pytest, Vitest/Testing Library and project-local Playwright.

Use supported libraries for authentication primitives, model integration and graph persistence.
Do not implement custom model HTTP clients or a reusable queue framework.
Pin compatible versions and commit lockfiles after checking compatibility.
The RTX 3060 is not required; live providers are the primary AI path.

Development clarification (2026-09-08): the user has no API key and requests simulated generation
API data with Codex-assisted answers. Document parsing, chunking, local multilingual embedding,
PostgreSQL vector indexing and retrieval must be real. Implement the development provider behind
the same internal contract, label its provenance, and preserve the real OpenAI integration path.
Local CPU embeddings are authorized for this purpose. Neither development handoffs nor mocks
prove external API connectivity, generation latency, billing or live-provider quality.

For a local release, build frontend assets and serve them from FastAPI at the same origin.
This reduces release services to app, worker and PostgreSQL. Keep Vite for development.
Bind local ports to loopback. Remote/public deployment requires a separate contract.

## 6. Durable jobs without Redis

Use a small jobs table in PostgreSQL. Save the business record and its pending job in the
same transaction. The API returns a record/job ID promptly; the worker polls for work.

- Atomically claim an eligible job with a short row-lock transaction and a lease token.
- Use `FOR UPDATE SKIP LOCKED` for competing claims; never hold a database transaction
  open during a model request. PostgreSQL documents this mechanism for queue-like tables:
  [SELECT locking clauses](https://www.postgresql.org/docs/current/sql-select.html).
- Store state, attempt count, available time, lease expiry, heartbeat and diagnostic error.
- Heartbeat long work; fence writes with the current lease token so an expired worker
  cannot overwrite a successor's result.
- Reconcile expired leases on worker startup and periodically. Bound retries and backoff.
- Claim one job at a time initially. Prioritize interactive support over queued evaluation
  and ingestion; already-running work is not preempted.
- Cancellation is cooperative at safe boundaries. Show cancellation requested until confirmed.
- Give duplicate submissions an idempotency key bound to their payload. Replays reuse the
  original result; changed payloads with the same key fail explicitly.
- Check actor membership and resource scope before queued work exposes data to a provider.

The jobs table owns scheduling. LangGraph checkpoints own workflow continuation. Domain
records own user-visible results. Document the boundaries instead of maintaining competing
state machines in multiple services.

Use supported durable LangGraph checkpointing in PostgreSQL. Human review releases the
worker; an authorized decision schedules resume. Nodes and result publication must tolerate
replay. See [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

Do not promise exactly-once external model execution. A crash after provider dispatch may
leave an uncertain charge; preserve that uncertainty, bound retry and avoid duplicate publication.

## 7. Knowledge and multilingual RAG

Ingestion: persist original → validate/decode → normalize → split → embed → ready.

- V1 accepts UTF-8 TXT/Markdown, including BOM; reject unsupported encodings clearly.
- Initial limits: 5 MiB per file, 500 active documents and 50,000 chunks per workspace.
  These are resource limits, not demonstrated capacity claims; measure the supported profile.
- Preserve original content, checksum, headings, section metadata and processing errors.
- Use established splitting utilities with EN/JA/ZH-aware separators and bounded overlap.
- Batch embedding requests with per-call token limits and complete usage records.
- A replacement version becomes active only after indexing succeeds. The previous active
  version remains available meanwhile; explain this in the UI.
- Withdrawal immediately excludes the document from new retrieval. Historical citations
  retain their exact evidence, with a withdrawn/superseded label.
- Keep deletion/retention policy explicit; do not destroy referenced historical versions.

Retrieval:

Historical implementation note (2026-09-09, checkpoint `2379915`): that search selected 20 cosine
candidates and uses a local multilingual neural reranker. The measured need and frozen-corpus
results are recorded in [M2](docs/plans/active/m2-real-retrieval.md). Steps 3–4 below describe
the release requirement, not code at that checkpoint. The user's earlier topology names BM25 candidates;
the subsequent audit brief requires measured lexical/hybrid comparison. See [RAG design](docs/RAG.md).
BM25/fusion parameters remain a measured design choice; reranker results do not complete this work.
Current explicit BM25/hybrid strategies and candidate inspection are tracked in the
[hybrid plan](docs/plans/active/m2-hybrid-retrieval.md). The default remains vector-rerank;
the shared development-corpus comparison supports retaining it. Held-out comparison and
the remaining release gates are incomplete.

1. Apply workspace, active-version and allowed-knowledge filters before model context.
2. Use database-side exact pgvector search, not application-side scanning of all vectors.
3. Retrieve independent BM25 candidates with documented Unicode-aware EN/JA/ZH behavior.
4. Combine vector and BM25 rankings using measured rank fusion, retaining separate raw scores.
5. Deduplicate and select evidence within a token budget, retaining citation provenance.

Retrieve across permitted source languages; do not filter out English policies for Japanese
questions. Record embedding provider, model and dimensions; never mix incompatible spaces.
Do not label simple token overlap as semantic understanding. Evaluate lexical and fusion
behavior before tuning it. No reranker or new search service without a measured requirement.

Knowledge detail includes a “Test this knowledge” action showing retrieved passages for a
question. It must use the actual retrieval service, with optional document restriction.

## 8. LangChain and LangGraph responsibilities

LangChain supplies useful model, splitter, structured-output and retrieval components.
LangGraph coordinates the governed support workflow:

validate_input → determine_language/intent → retrieve_evidence → pack_context →
draft_response → validate_support/policy/tone → route → finalize or wait for review.

Clarification and insufficient evidence may exit before drafting. All exceptions become
explicit failures with retained evidence. Nodes may be deterministic; stages are not agents
and do not each require an LLM call.

- Default to one draft call; use a bounded validation call only when justified by its task.
- No open-ended agent loops or recursive delegation inside the product.
- Preserve the original message, requested language, selected configuration and prompt version.
- Ground company-policy claims in authorized retrieved evidence.
- Validate citation identifiers and claim support separately; valid IDs alone are insufficient.
- Label any confidence score as heuristic unless calibrated; show concrete review reasons.
- Customer text and documents are data, never authority over prompts, permissions or tools.
- Review preserves original draft, edited response, actor, decision, reason and timestamps.
- Use optimistic concurrency/version checks so conflicting reviewers cannot both finalize.
- Clarifications and retries create linked attempts without overwriting the original input.
- Store observable artifacts and concise decision reasons, not private chain-of-thought.

## 9. Persistence, security and accounting

Use the smallest schema covering identities/memberships, messages/imports/labels, documents/
versions/chunks, runs/steps/reviews, model calls, jobs, checkpoints and evaluations.
Do not create a table for every conceptual noun or duplicate entire graph state in every step.

- Enforce workspace ownership and reject cross-workspace references in services and constraints.
- Never trust client/queue identity fields; derive identity from authenticated server context.
- Prefer same-origin HttpOnly session cookies with appropriate CSRF protection and expiry.
- Hash passwords with a maintained password-hashing implementation; redact secrets from logs.
- Authenticate original downloads, source previews, traces and evaluation artifacts.
- Record each model/embedding attempt, provider/model, reported/estimated tokens, pricing
  version, estimated cost, duration and success/failure/uncertain status.
- Correlate request → job → run → step → retrieval/model call.
- Enforce configured token/call/spend limits before dispatch, not just after completion.
- Live evaluation budget defaults to zero. Keys alone do not authorize spending.
- Keep raw customer content out of operational logs; access-controlled original records are
  distinct from logs. Use synthetic data in committed fixtures and default demos.
- Use PostgreSQL backups for authoritative data; verify restoration into an isolated database.

## 10. Repository and documentation

Start from `codex/fresh-start`. Historical code remains on
`archive/previous-platform-2026-09-08`; it is reference material, not a scaffold to restore.
Preserve old secrets, databases, backups and ignored local directories. Use a distinct Compose
project, database, volumes and ports. Never reset or delete previous application data.

### Target project topology

For implemented paths and runtime flow, see [current architecture](docs/ARCHITECTURE.md).
This target tree includes modules that do not exist yet.

This is the intended structure, not a request to generate empty directories. Create each
module during its owning milestone. The API and worker share the same backend package.

```text
AgenticSupportIntelligencePlatform/
├── REBUILD_PLAN.md                 # Product scope and release contract
├── AGENTS.md                       # Concise instructions for coding agents
├── README.md                       # Verified setup and operator demo
├── compose.yaml                    # Local app, worker, database; dev frontend
├── .env.example                    # Documented configuration; no secrets
├── .gitignore
├── .dockerignore
│
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile                  # Shared API/worker runtime
│   ├── alembic.ini
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/               # Reviewed, ordered schema migrations
│   ├── app/
│   │   ├── main.py                 # FastAPI composition and route registration
│   │   ├── worker.py               # Worker startup and graceful shutdown
│   │   ├── core/                   # Settings, sessions, errors, logging, security
│   │   ├── db/                     # Engine, transaction/session helpers, model registry
│   │   ├── modules/
│   │   │   ├── identity/           # Login/logout, password verification, user identity
│   │   │   ├── workspaces/         # Membership, roles and workspace access checks
│   │   │   ├── conversations/      # Original messages, JSONL import and labels
│   │   │   ├── knowledge/          # Uploads, versions, ingestion and source previews
│   │   │   ├── retrieval/          # Scoped vector/lexical queries and rank fusion
│   │   │   ├── support/            # Run admission, attempts, results and cancellation
│   │   │   ├── reviews/            # Review decisions and concurrency enforcement
│   │   │   ├── evaluations/        # Baseline execution, metrics and comparisons
│   │   │   └── usage/              # Model-call ledger, budgets and usage summaries
│   │   ├── workflows/
│   │   │   ├── support_graph.py    # LangGraph nodes, edges and conditional routing
│   │   │   ├── state.py            # Typed workflow state and outcomes
│   │   │   ├── checkpoints.py      # Supported PostgreSQL checkpoint integration
│   │   │   └── nodes/              # Focused adapters calling application services
│   │   ├── providers/
│   │   │   ├── contracts.py        # Narrow generation/embedding interfaces
│   │   │   ├── openai.py           # Maintained SDK/LangChain integrations
│   │   │   └── fake.py             # Explicit offline-test provider
│   │   ├── jobs/
│   │   │   ├── models.py           # Durable PostgreSQL job records
│   │   │   ├── repository.py       # Atomic claims, leases and fenced updates
│   │   │   ├── runner.py           # Polling, dispatch, heartbeat and bounded retry
│   │   │   ├── recovery.py         # Expired-lease reconciliation
│   │   │   └── handlers.py         # Ingestion/support/evaluation service entry points
│   │   └── prompts/               # Versioned draft and validation prompt templates
│   └── tests/
│       ├── conftest.py             # Isolated fixtures and explicit provider overrides
│       ├── unit/                  # Pure validation, ranking, routing and budgeting
│       ├── integration/           # Real PostgreSQL/pgvector and worker behavior
│       └── security/              # Roles, workspace isolation and untrusted inputs
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── Dockerfile                 # Vite development service
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── playwright.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── app/                   # Router, layout, session and workspace context
│   │   ├── api/
│   │   │   ├── client.ts          # Shared HTTP/error/cancellation handling
│   │   │   └── generated.ts       # Types generated from backend OpenAPI
│   │   ├── components/            # Shared accessible controls and display primitives
│   │   ├── styles/                # Design tokens, global styles and responsive rules
│   │   └── features/
│   │       ├── auth/              # Sign-in and expired-session experience
│   │       ├── workbench/         # Inbox, import, labels, message detail and review
│   │       ├── knowledge/         # Upload/status, versions and evidence drawer
│   │       ├── quality/           # Evaluation results and aggregate usage
│   │       └── settings/          # Members, processing defaults and provider readiness
│   └── tests/
│       ├── components/            # Vitest/Testing Library interaction tests
│       └── e2e/                   # Real application journeys through Playwright
│
├── evals/
│   ├── fixtures/
│   │   ├── policies/              # Substantial synthetic TXT/Markdown policies
│   │   └── conversations/         # Separate untrusted customer-message fixtures
│   ├── cases/                     # Fixed EN/JA/ZH expected facts and permitted sources
│   └── rubrics/                   # Human-readable scoring and review criteria
│
├── scripts/
│   ├── manage.py                  # Cross-platform command dispatcher
│   ├── doctor.py                  # Dependencies, configuration, ports and provider mode
│   ├── seed_demo.py               # Idempotent synthetic two-workspace data
│   ├── verify.py                  # Fast, integration, browser and live check entry points
│   ├── evidence.py                # Revision/configuration/results evidence manifest
│   └── recovery.py                # Backup and isolated restoration verification
│
├── infra/
│   └── Dockerfile.release         # Build web assets; serve via non-root FastAPI image
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ACCEPTANCE.md
│   ├── STATUS.md
│   ├── RUNBOOK.md
│   └── plans/                     # Only for meaningful multi-session work
│       ├── active/
│       └── completed/
├── .github/
│   └── workflows/
│       └── verify.yml             # Automated checks; no deployment or default live spend
└── .artifacts/                    # Ignored logs, screenshots, traces and local backups
```

### Module boundaries

Within a backend domain module, start with the files its behavior actually requires:

```text
modules/knowledge/
├── routes.py       # HTTP contracts; authentication and permission dependencies
├── schemas.py      # Request/response validation
├── models.py       # Domain tables and database constraints
├── service.py      # Application rules and transaction coordination
├── repository.py   # Workspace-scoped persistence queries, when extraction is useful
└── ingestion.py    # Document processing; split further only when necessary
```

Other modules follow the same responsibility boundaries without needing identical filenames.
Graph nodes and job handlers call these services; they do not duplicate business rules.
Modules use explicit service calls instead of importing another module's route handlers.
Domain models remain in their modules; `db/` holds infrastructure and model registration.
Operational logging belongs in `core/`; business usage and accounting belong in `modules/usage/`.

Inside a frontend feature, separate page/components, hooks and feature API calls as needed.
Feature API calls use the shared client and generated types. Components do not orchestrate
multi-step backend workflows. The backend owns decisions; the UI renders their persisted state.

Dependencies flow from routes/job handlers/graph nodes into services, then repositories and
provider interfaces. Framework startup composes dependencies; avoid circular module imports.
No Redis configuration, queue broker, cloud SDK layer or general-purpose orchestration platform
belongs in this topology.

Organize modules by responsibility. Separate rendering, state, network access, validation,
business logic and persistence when that separation helps. Keep files cohesive, normally
under 300 lines. Avoid generic frameworks, empty module hierarchies and parallel implementations.

Initially this plan is the product/release contract. Add only:

- `AGENTS.md`: concise director for scope, routing and coordination; no implementation recipes.
  Each substantive area owns a linked local `AGENTS.md` for its rules and verification guidance.
  The runbook owns working commands; design documents own implementation details.
- `README.md`: setup and verified demo, updated as commands become executable.
- `docs/ARCHITECTURE.md`: actual components, state ownership and durable decisions.
- `docs/ACCEPTANCE.md`: stable gates and associated checks.
- `docs/STATUS.md`: current milestone, evidence, limitations and next action.
- `docs/RUNBOOK.md`: operation, recovery and verified restore procedure.

Use short execution plans only for meaningful multi-session work. Do not duplicate policies
across many files. Use only OpenAI-provided Codex tools/skills; do not add custom skill bundles.

Provide a cross-platform entry point, proposed as `python scripts/manage.py`, with doctor,
up, migrate, seed-demo, verify-fast, verify, verify-live, evidence, backup, restore-test and down.
Implement commands before documenting them as working. Optional Make targets may wrap them;
Make, WSL and a personal Chrome extension must not be required for verification.

## 11. Acceptance and evaluation

| ID | Required evidence |
| --- | --- |
| BOOT | Fresh isolated setup starts, migrates and passes readiness checks |
| AUTH | Login/logout/expiry, role denial and last-admin protection |
| TENANT | Foreign-workspace read/write/retrieval/artifact/queued-job access denied |
| KNOW | Upload/index/test/replace/withdraw with exact original and version preservation |
| RAG | Real retrieval returns expected sources; answers contain supported facts/citations |
| LANG | EN/JA/ZH outputs and cross-language evidence cases pass |
| ROUTE | Clarification, insufficient/conflicting evidence, review and failure stay distinct |
| REVIEW | Approve/edit/reject persists; duplicate/concurrent decisions cannot double-finalize |
| JOB | Restart, expired lease, duplicate admission and cancellation preserve correct state |
| DATA | Import, label, select and process customer messages form a connected workflow |
| TRACE | Displayed model, evidence, timing and usage agree with persisted records |
| EVAL | Four distinct pipelines run the same cases with comparable settings |
| UX | Core journeys, keyboard flow, narrow layouts, zoom and error states pass in browser |
| RESTORE | Restored data matches backup and the restored app processes a new request |

Create coherent synthetic company policy documents with exceptions, cross-references, updates
and conflicting historical versions. Target 30–50 pages equivalent of readable TXT/Markdown,
not repetitive filler; PDF generation is not needed. Cover billing/refunds, service eligibility,
escalations and privacy boundaries. Label all policies synthetic.

Use at least ten fixed cases per language, including paraphrases, cross-language evidence,
missing information, policy conflicts, prompt injection and required review. Keep expected
facts/permitted sources separate from application code. Never add fixture-specific answer logic.

Compare direct_llm (no retrieval), vector_rag (vector retrieval), hybrid_rag (vector plus BM25),
and system_v1 (hybrid plus governed workflow). Keep generation settings comparable and record differences.
Freeze retrieval/answer/citation targets and latency budgets before tuning; do not force a
baseline to lose. Report counts and denominators per language, with representative outputs.

Verification layers:

- Fast: lint, types, unit/component checks and pure ranking tests.
- Integration/security: real PostgreSQL/pgvector and worker behavior.
- Offline browser: real UI/API/database/worker; only external providers are deterministic fakes.
- Live: authorized, budgeted model and embedding calls against the fixed corpus.
- Human review: representative answers, source support and usability inspection.

For this small release, test five concurrent operator sessions and bounded background work;
record corpus size, queue wait, response latency and ingestion duration. This defines the
tested local profile, not an enterprise scale claim. Bound payloads and paginate all lists.

## 12. Delivery order and stopping rules

| Milestone | Deliverable and gate |
| --- | --- |
| M0 | Confirm isolation, concise contract, initial fixtures and executable doctor |
| M1 | Local stack, auth, workspace roles, migrations and first real browser journey |
| M2 | TXT/Markdown → worker → real embeddings → ask → cited draft → source inspection |
| M3 | Clarification, review, cancellation, retries, recovery and durable checkpoints |
| M4 | Import/labels, version management, usable responsive workbench and minimal settings |
| M5 | Four evaluation pipelines, per-language results and compact usage view |
| M6 | Fresh-install, full browser/security/live checks, restoration and release evidence |

Observability and tests begin in M1. Real authorized local models can supply local-live evidence;
external-provider gates remain unverified without access/spending authority. Never count mocks
as model-quality evidence or local inference as proof of external API connectivity.
Complete the first usable RAG flow before building Quality or adding secondary administration.

Use one implementation owner. Delegate bounded read-only review only when it improves evidence.
For each slice: identify acceptance IDs → implement → verify the actual flow → fix confirmed
defects → checkpoint → update status. Do not manufacture new tasks after the contract is met.

Target 30–60-minute slices. Reassess at 90 minutes; diagnose afresh after three failed repairs.
The user removed the fixed execution time limit on 2026-09-10 (Tokyo). Continue within the
authorized goal and preserve exact resume instructions at checkpoints. A missing parser,
browser or provider check stays visibly blocked/unverified rather than becoming a pass.

Resolve routine choices without repeated confirmation. Ask for credentials/access, explicit
live spending, destructive changes, or material scope/security/architecture changes. Maintained
dependencies needed by the approved stack are permitted once this plan becomes the active goal.
Do not install third-party Codex skills. Commit and push each coherent verified slice to the
working rebuild branch. Merges, public deployment and migration of old data require separate
authorization. Follow DEVELOPMENT for staged review, remote confirmation and CI feedback.

## 13. Definition of done

Deliver the exact revision, acceptance matrix, commands/results, browser screenshots/traces,
provider mode, live spend estimate, fixed-case evaluation results, restoration evidence,
remaining limitations and a short operator demo.

Distinguish VERIFIED_LOCAL_OFFLINE, VERIFIED_LOCAL_LIVE, PARTIALLY_VERIFIED/BLOCKED and
AWAITING_HUMAN_RELEASE_REVIEW. Do not claim general production readiness.

The release is complete only when the scoped acceptance gates pass and the operator can
reliably move from a real message and trusted knowledge to an inspectable, reviewed response.
Stop there. Additional formats, integrations or scale are a separate release decision.
