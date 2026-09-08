# Production readiness and OpenAI workflow review

Reviewed: 2026-09-07. Local HEAD: `18a977fe4834d39545d71a1e271dd9913cf82a83`.

This is a source review, not a production certification or a completed penetration test. Runtime validation was blocked by the local environment. No application implementation was changed. The pre-existing untracked `docs/tickets/run-budget-reservations.md` was preserved.

## Assessment

The repository is a substantial local-first prototype with useful backend boundaries, permission dependencies, domain tests, model-call accounting, prompt provenance, and resource management. It does not yet meet the requested production release bar. The greatest gap is between written engineering rules and executable enforcement, followed by AI evaluation validity, spending controls, and operational reliability.

Treat production readiness as a bounded release target: a small internal team, a declared workload, private deployment, explicit data handling rules, controlled provider spending, observable failures, and tested recovery. Enterprise SSO, Kubernetes, a separate vector database, and million-record scale are not automatic prerequisites.

## OpenAI guidance and its application

The user's two sources describe practices and an engineering experiment, rather than a universal certification standard.

- [How OpenAI uses Codex](https://openai.com/business/guides-and-resources/how-openai-uses-codex/) recommends scoped tasks, planning before large changes, persistent repository context, and improving the agent's development environment. This project already documents much of that loop; the local execution environment still needs work.
- [Harness engineering](https://openai.com/index/harness-engineering/) emphasizes discoverable repository knowledge, runnable application feedback, mechanical architecture checks, and continuous maintenance. My recommendation is to translate those principles into CI checks, reproducible environments, and evidence attached to each ticket. Copying the article's permissive merge approach is not a prerequisite.

The remaining recommendations below are this review's application of those ideas to the inspected code, not requirements quoted from OpenAI.

## README claim audit

| Claim | Source assessment | Missing evidence or correction |
| --- | --- | --- |
| Authentication and workspace isolation | Implemented dependencies and permission tests exist; current roles exceed the old README summary | PostgreSQL-backed cross-workspace and role-matrix regression gates; production credential configuration |
| Dataset curation | Import, language detection, labels and management paths exist | Full multilingual browser acceptance path and realistic import limits/failure testing |
| Knowledge ingestion | Versions, chunks and deterministic embeddings exist | Real semantic embedding adapter, explicit active-version retrieval policy |
| Hybrid retrieval and citations | Workspace-filtered candidates are scored by vector and lexical code | Database-side bounded retrieval, meaningful semantic vectors, answer-to-source validation |
| LangGraph workflow | Actual StateGraph execution and stored steps exist | Durable resumption and crash recovery are not established by stored JSON checkpoints |
| Human review | Claim, release and resolve paths exist | Atomic competing claims/decisions, verified concurrent behavior |
| Evaluation across three modes | Modes and metrics are stored | Baselines are not comparable model pipelines; metrics do not establish factual grounding |
| Token/cost observability | Model-call ledger and provider usage parsing exist | Hard runtime spending limits, bounded output, interrupted-call reconciliation |
| Full browser demo | UI and three Playwright tests exist | Entire README journey is not a required CI test |
| Mock-only model providers | README is stale | Configured OpenAI-compatible transport now exists; distinguish model and embedding status |
| Audit logs postponed | README is stale | Audit services and routes exist; document current coverage and remaining gaps |

## Prioritized findings

P1 below means a blocker for the proposed production target, not necessarily an exploitable emergency in a private local demo. Concurrency and crash scenarios are source-derived risks requiring runtime reproduction.

### 1. P1: Production secrets are not fail-closed

`backend/app/core/config.py:11` defaults to a known JWT signing secret. `docker-compose.yml` does not override it, and configuration has no non-local rejection guard. A deployment that inherits these defaults does not have a defensible authentication boundary. The Compose file also publishes database and Redis ports with local credentials.

Add explicit local and production profiles, reject default/missing production secrets at startup, restrict exposed ports, and test configuration failures. Review login abuse protection and token revocation requirements separately; the existing agent-run quota is not an authentication throttle.

### 2. P1: Product budgets are not enforced before model calls

`backend/app/services/agent_service.py:213` computes the effective run token budget and passes it into state. The graph does not use that value for admission. `model_call_planning.py` and `token_budget.py` check individual model context estimates, while workspace monthly/per-run spending settings are not enforced in that execution path.

`model_provider.py:81` sends a request without an output-token cap. Planning against the synthetic completion text therefore cannot cap actual provider output.

Use the existing reservation ticket as a starting point. Add transactional admission, bounded output, usage reconciliation and expiry for abandoned reservations. Cover concurrent requests with PostgreSQL tests. Extend the design to every billable call path, including evaluation; the existing ticket explicitly excludes non-agent evaluation calls.

### 3. P1: Evaluation can report quality without measuring it

`backend/app/services/evaluation_runner.py:349` uses a mock provider for `direct_llm`. The `vector_rag` branch uses the hybrid retrieval service and a canned answer without a generation call. `system_v1` uses the configured agent pipeline. These are not controlled comparisons when the system uses a real provider.

At `evaluation_runner.py:457`, groundedness is satisfied by citation presence for finalized cases. Citation accuracy accepts any expected-source substring match. Neither proves that the answer is supported by the cited passage. `guardrails.py` similarly checks evidence presence rather than claim support.

Separate deterministic regression tests from real quality evaluation. Make each baseline implement its advertised algorithm under matched model, dataset and budget conditions. Add exact source IDs, answer-support rubrics, adversarial unsupported answers, and human-reviewed EN/JA/ZH holdouts. Version model/prompt/corpus/evaluator inputs and publish sample counts and uncertainty. Keep automated software tests mocked.

### 4. P1: Review ownership and resolution are check-then-write

`backend/app/services/human_review_service.py:157` and `:183` read state, check it in Python and later commit updates. There is no row lock, revision check or conditional update in these paths. Two concurrent sessions can both see a pending/unassigned review and overwrite ownership or resolution.

Add an atomic transition with a conflict result. Test two simultaneous claims and conflicting resolutions on PostgreSQL, including final graph state, checkpoint and audit consistency.

### 5. P1: Traces do not establish durable execution

`backend/app/services/support_agent_graph.py:73` compiles and invokes without a LangGraph checkpointer. `_record_checkpoint` persists application JSON after steps. Human review directly updates the graph run rather than resuming a suspended graph.

`agent_service.py:220` commits a running record before graph execution. Unexpected failures around graph execution have no enclosing recovery transition there. Many services commit independently; a process failure can leave partial workflow state. The AI ledger is recorded after the external call returns, so a crash between provider success and persistence can lose usage evidence.

Specify the supported recovery contract first. Implement durable job/run IDs, idempotency, started/finished attempt records, stale-run reconciliation and restart tests. Use a durable checkpointer if resumption is required. A JSON trace snapshot should be documented as such until it is replayable.

### 6. P1: Required validation does not protect the actual runtime

`backend/tests/conftest.py:61` uses SQLite and `Base.metadata.create_all`, bypassing production PostgreSQL behavior and Alembic migration execution. `.github/workflows/ci.yml` does not run PostgreSQL integration or Playwright jobs. `frontend/package.json` defines `test` as TypeScript checking.

Keep fast SQLite/unit tests where useful, but add real PostgreSQL/pgvector tests and migration checks. Run the full demo journey with at least two workspaces and multiple roles in CI. Include forbidden actions, source isolation, review completion and provider failure. Add focused frontend behavior tests as boundaries are extracted. Type checking should remain a separately named check.

### 7. P2: Large modules contradict repository rules

Physical line counts at review time:

| File | Lines |
| --- | ---: |
| `frontend/src/app/AppShell.tsx` | 8,111 |
| `frontend/src/pages/AgentsPage.tsx` | 939 |
| `backend/app/services/support_agent_graph.py` | 870 |
| `backend/app/services/agent_service.py` | 787 |
| `backend/app/api/v1/agents.py` | 660 |

The shell contains API transport (`:1018`), response types, authentication persistence (`:1209`), feature state, orchestration and rendering. Page extraction alone has not removed the shared state coupling.

Split one tested feature at a time: UI components, feature hooks, API modules, boundary schemas, backend orchestration, persistence helpers and tests. Do not create a new giant generic hook or service. Add import-boundary checks and a file-size ratchet that prevents growth of legacy oversized files while allowing incremental cleanup. New files should follow the existing approximately 300-line rule with explicit exceptions.

### 8. P2: Retrieval is synthetic, unbounded and version-ambiguous

`embedding_provider.py` derives 16-dimensional vectors from SHA-256; these are deterministic test fixtures, not semantic embeddings. `retrieval_service.py:172` loads all matching candidates into Python, scores and sorts them before applying top-k. pgvector storage does not mean indexed vector search is being used.

The candidate query does not restrict document versions to the latest or active version. Reindexing creates a new version while preserving old versions, so old policy chunks remain eligible for retrieval.

Add an explicit published version boundary, exact citation identifiers, real embedding configuration and a dimension/version migration plan. Move bounded scoring into PostgreSQL when justified by a measured target workload. Preserve workspace predicates before ranking. Test a policy correction where the superseded answer must no longer be returned.

### 9. P2: Guardrails need adversarial and privacy evidence

`guardrails.py` checks a short marker list against the user message. That does not establish resistance to paraphrases, multilingual attacks or malicious retrieved documents. Checkpoints and retrieval traces retain source/user content; a prompt hash in the AI ledger does not provide a system-wide PII guarantee.

Define data classification, retention, deletion, trace access and external-provider disclosure rules. Validate tool inputs/outputs, keep authorization deterministic, and add poisoned-document and cross-workspace red-team cases. Require human review for the chosen high-risk workflows and measure false positives as well as misses.

### 10. P2: Deployment and operations remain development-oriented

`frontend/Dockerfile` runs Vite's development server. `backend/Dockerfile` runs migrations during API startup and has no non-root user declaration. `/health` is liveness only; the authenticated system-health service contains some deeper checks, but this does not establish deployment readiness or monitoring.

Build and serve production static assets, separate migration execution from replicated API startup, define readiness and graceful shutdown, and establish backups with a demonstrated restore. Add structured request/run correlation, operational metrics, alert thresholds, rollback instructions and a bounded load test. Choose measurable latency, availability, concurrency, recovery and spending targets before claiming production readiness.

### 11. P2: Repository knowledge lacks a freshness contract

The README's mock-only statement, audit limitation and 54-test validation snapshot are stale or ambiguous. Earlier audits also describe obsolete role and UI limitations. The current 77-line repository AGENTS.md is appropriately compact, but global guidance and several project documents duplicate process rules.

Keep one current capability matrix mapping each promise to implementation, automated evidence, limitations, owner and verification date. Mark older audits as historical or superseded. Generate API/schema references where practical. Add doc-link validation and a review checklist for behavior changes. Avoid adding more unmaintained checklists.

## Recommended execution order

1. **Verification foundation:** Make a clean checkout runnable through one documented environment; add PostgreSQL migration/integration and browser CI gates. Capture baseline results without changing acceptance assertions to make failures disappear.
2. **Safe real-provider execution:** Reject unsafe production configuration; implement budget reservations/output limits and atomic human-review transitions in separate tickets.
3. **Truthful AI behavior:** Correct baseline algorithms and quality metrics; establish the multilingual holdout and active-document-version policy; validate real embeddings in controlled experiments.
4. **Incremental architecture recovery:** Extract one domain from the shell and one graph responsibility at a time behind behavior tests; enforce boundaries and size ratchets.
5. **Operational release:** Demonstrate restart recovery, bounded load, deployment, rollback and backup restoration for the declared internal-team workload.

Each item is a milestone containing several small tickets, not permission for a broad implementation pass. Preserve human review of scope, architecture, security decisions and merges.

## Working contract for future Codex tasks

- Use only OpenAI-provided tools and skills, following the user's updated policy.
- A ticket names one user-visible outcome, non-goals, boundaries and failure cases.
- Acceptance evidence includes the relevant commands, permission-denial cases and screenshots/traces for browser behavior.
- CI enforces checks; prose reminders alone are insufficient.
- Convert recurring review failures into targeted tests or lint rules.
- Keep active decisions and task status in the repository; do not rely on chat memory.
- Do not commit or merge without the user's authorization.

## Validation attempted

| Command | Result |
| --- | --- |
| `uv run --offline --no-sync pytest -q` in backend | Blocked by uv cache permission denial |
| `uv run --offline --cache-dir .review-uv-cache --no-sync pytest -q` in backend | Blocked by incompatible/inaccessible existing `.venv/lib64` |
| `npm.cmd test` in frontend | Could not run TypeScript: `tsc` unavailable |
| `docker compose ps` | Docker daemon pipe unavailable; Docker configuration access also denied |

No test pass count, live quality score, browser acceptance result or production readiness claim is asserted. GitHub branch protection, hosted CI results and deployment configuration were not inspected. The two OpenAI articles were fetched; gstack failed to start before the user's instruction to remove third-party skills.
