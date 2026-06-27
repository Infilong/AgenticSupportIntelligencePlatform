# Milestone Plan

Do not code all milestones at once. For each milestone: create a plan, wait for approval, implement, add tests, run validation, explain the diff, update docs, create a learning note, and stop for review.

## Milestone 0: Planning And Governance
Deliverables:
- `AGENTS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/PLANS.md`
- `docs/product-spec.md`
- `docs/architecture.md`
- `docs/database-schema.md`
- `docs/api-design.md`
- `README.md` draft
- `docs/learning/README.md`
- focused design docs for RAG, LangGraph, tools, token economy, evaluation, security, observability, scale, tradeoffs, and Codex workflow

Acceptance criteria:
- architecture is clear
- scope is divided into Phase 1, Phase 2, and postponed features
- repo rules are explicit
- Codex workflow is documented
- no application code exists yet

Human review checklist:
- Is the product story sharp?
- Is Phase 1 achievable?
- Are APIs workspace-scoped?
- Are tests required from the start?
- Are fake implementations forbidden?
- Is the portfolio narrative strong?

## Milestone 1: Project Skeleton
Deliverables:
- backend FastAPI app
- frontend skeleton
- Docker Compose
- PostgreSQL
- Redis
- pgvector extension setup
- pytest setup
- ruff setup
- health endpoint
- Makefile
- GitHub Actions CI

Acceptance criteria:
- `docker compose up` works
- `GET /health` returns OK
- backend tests pass
- CI runs tests
- README has local setup steps

## Milestone 2: Auth And Workspace Isolation
Deliverables:
- user model
- workspace model
- workspace member model
- JWT auth
- protected endpoints
- workspace permission dependency
- permission tests

Acceptance criteria:
- users can register/login
- users can create workspaces
- protected endpoints reject unauthenticated users
- users cannot access another workspace
- tests cover permission denial

## Milestone 3: Dataset Import And Multilingual Examples
Deliverables:
- dataset model
- import batch model
- conversation example model
- message model
- label model
- CSV/JSONL import
- language detection for en/ja/zh
- label editing API
- seed demo examples

Acceptance criteria:
- import multilingual examples
- language is stored
- labels can be edited
- examples are workspace-scoped
- tests cover import, language detection, labels, permissions

## Milestone 4: Knowledge Document Ingestion
Deliverables:
- document model
- document version model
- document chunk model
- upload API
- async worker
- parsing
- language-aware chunking
- embedding provider abstraction
- mock embedding provider for tests
- pgvector storage

Acceptance criteria:
- upload creates document
- worker chunks and embeds
- document status updates
- unsupported file type rejected
- long document is not sent to LLM
- tests cover worker success/failure

## Milestone 5: Retrieval And Citations
Deliverables:
- vector search
- lexical search
- hybrid retrieval
- metadata filtering
- citation generation
- retrieval trace storage
- retrieval API
- no-source detection

Acceptance criteria:
- search returns cited chunks
- retrieval traces are stored
- cross-workspace retrieval is impossible
- Japanese/Chinese lexical limitations are documented
- tests cover retrieval, citations, no-source, permissions

## Milestone 6: AI Run Ledger And Token Budget Planner
Deliverables:
- model config
- AI run ledger
- token/cost estimator
- token budget planner
- cache entry model
- cost summary API
- mock model provider

Acceptance criteria:
- every model call creates an AI run
- token/cost/latency fields are recorded
- budget enforcement works
- long context is filtered/compressed before model call
- tests cover cost calculation and budget denial

## Milestone 7: LangGraph Support-Agent Workflow
Deliverables:
- graph state
- graph nodes
- graph run model
- graph step model
- tool call model
- checkpoint support
- basic tools: search_documents, get_document_chunk, compare_policy, draft_response, calculate_cost

Acceptance criteria:
- graph run stores every step
- workflow detects language
- retrieves evidence
- drafts same-language response
- stores tool calls
- stores AI runs
- trace endpoint returns full graph execution
- tests cover graph routing and failures

## Milestone 8: Guardrails And Human Review
Deliverables:
- prompt injection guardrail
- citation-required guardrail
- unsupported answer refusal
- unsafe tool blocking
- language preservation check
- confidence scoring
- human review model
- human review API
- review routing

Acceptance criteria:
- low-confidence cases route to review
- high-risk cases route to review
- missing citations route to review or refusal
- prompt injection is blocked
- reviewer can approve/edit/reject
- tests cover all routing paths

## Milestone 9: Evaluation Runner
Deliverables:
- evaluation case model
- evaluation run model
- evaluation result model
- JSONL evaluation loader
- metrics calculation
- baseline modes: direct LLM, vector-only RAG, system v1
- per-language metrics

Acceptance criteria:
- evaluation can run from API or command
- metrics are stored
- English/Japanese/Chinese results separated
- baseline comparison works
- tests cover evaluation schema and metrics

## Milestone 10: Frontend Trace And Evaluation UI
Deliverables:
- login UI
- workspace dashboard
- dataset import page
- document upload page
- agent run page
- graph trace viewer
- evaluation dashboard
- cost dashboard
- human review page

Acceptance criteria:
- user can run full demo from browser
- graph trace viewer is clear
- evaluation dashboard shows per-language metrics
- cost dashboard shows token/cost/latency
- UI does not need to be beautiful, but must be professional and usable

## Milestone 11: Portfolio Packaging
Deliverables:
- final README
- architecture diagram
- demo script
- screenshots or GIFs
- docs completed
- learning notes completed
- resume bullets
- known limitations section

Acceptance criteria:
- project can be understood in five minutes
- local setup works
- tests pass
- demo path works
- README clearly distinguishes implemented features from future scale path
