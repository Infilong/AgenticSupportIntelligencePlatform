# Service ownership map

`input_clarification.py` owns conservative incomplete-input preflight and localized clarification
text. `support_graph_builder.py` branches before language detection; `graph_outcome.py` publishes
awaiting_clarification without a review. `task_admission.py` and `task_attempt_context.py` serialize
clarification replies as linked attempts, preserving original input and recording the human actor.

`record_queries.py` owns scoped input-record list/detail queries over SupportTask/TaskExecution.
It groups retries under the original input and selects the latest attempt in SQL. API contracts
live in `app/schemas/record.py`; read-only routing lives in `app/api/v1/records.py`.
Record intake validation lives in `app/schemas/record_input.py`; the same records router also
admits new data through task_admission. Admission owns original-input preservation, authenticated
creator binding and idempotency. The source label supplied by a caller is not an authority claim.

Paths below are relative to this directory. This is a navigation map, not permission to load
every service into context. Start with the affected row and its tests.

`workspace_permissions.py` owns fixed and transitional legacy permissions.
`membership_authority.py` locks the workspace row and refreshes actor/target membership
before membership writes. `workspace_service.py` owns mutations and last-owner checks;
leave uses the same lock. Admins may only manage Viewer/Operator targets and assignments.
Owners retain privileged role management. PostgreSQL hierarchy tests cover competing
owner departures and stale actor authority; SQLite tests alone do not prove serialization.

`task_admission.py` admits durable support tasks and queued graph runs atomically with
configuration snapshots and caller-bound idempotency. `agent_run_context.py` supports
flush-only preparation so admission owns the commit. Task HTTP routes expose admission,
run state and stopping; the new browser Work flow uses the worker.
Admission also supports linked attempts through `task_attempt_context.py`: terminal parent,
one active attempt per task, current authority/budgets/configuration and bounded history.
`task_attempts` stores parent/correction/request-key metadata without changing old executions.
Corrections affect only the new prompt; history contains statuses/category/counts, not old
evidence excerpts. Retry API/UI is deployed on migration 0036. Identical approved notes for the same
task reuse the existing note under the task lock, with `reused` recorded in the tool result.
`review_outcome.py` owns reviewed status/output/checkpoint writes. New durable task rejection
uses Rejected; legacy synchronous runs preserve their earlier failed/human_rejected semantics.
`task_control.py` owns stop requests, audit and checkpoints in one transaction.
`task_actions.py` stages immutable internal category/note proposals and resolves exact-hash
approvals with current reviewer/initiator/agent checks. Task writes and their audit commit
together; repeated approval returns the stored result. Workspace/run locks serialize with
stop and membership changes. `graph_action_proposals.py` stages bounded proposals from
guarded classifier/draft outputs during publication; `action_review_gate.py` prevents
answer approval bypass and rejects pending actions with answer rejection or stopping.
`action_trace.py` flushes step/tool records inside the action transaction. Action HTTP
routes expose inspection and exact-hash resolution. Browser review controls and collapsed
execution records use these endpoints on migration 0035.
Queued/review-waiting tasks stop immediately; active tasks become Stopping until a
worker acknowledges. Task-backed review transitions lock the run after the review,
matching stop's lock order. PostgreSQL tests cover stop versus review publication.
`task_worker.py` owns one execution using a PostgreSQL session lock; node checks and
terminal records use that connection via `task_worker_control.py`. Graph topology lives
in `support_graph_builder.py`, leaving node implementations in the existing runner.
Interrupted runs fail without replay. `python -m app.worker` polls admitted work after
migration 0034; Compose starts it after API health succeeds.
Synchronous provider calls are not forcibly cancelled: stop takes effect before subsequent
nodes and publication, with Stopping shown until acknowledgment. Provider charges may remain.

`execution_ownership.py` owns a PostgreSQL session lock used by accounted embedding dispatch.
`embedding_attempts.py` commits admission/completion on that connection and preserves ownership
metadata. Read the [integration design](../../../docs/design-docs/interrupted-execution-ownership.md):
model calls are not integrated, and legacy pending attempts cannot be recovered from age alone.
`embedding_recovery.py` acquires orphan ownership, rechecks permissions/state and atomically
records the pending-to-uncertain transition with audit evidence; billing reconciliation is separate.

`evaluation_scoring.py` owns per-case acceptance and expected/actual behavior metadata;
`evaluation_metrics.py` owns mode/language aggregation. Untested optional checks do not enter
expectation-rate denominators. See the [metric contract](../../../docs/evaluation-design.md#optional-expectation-metrics).
`evaluation_usage.py` owns workspace/run-scoped model-ledger totals for system evaluations;
step totals are not prompt-token accounting. See [usage limits](../../../docs/evaluation-design.md#model-usage-accounting).
`evaluation_comparison.py` owns metric deltas and requires known matching score contracts per
mode/language group and matching case multisets. `evaluation_case_identity.py` fingerprints
loaded cases at scoring time; changed/unknown/mixed history has incomparable/null deltas.

`graph_step_ordering.py` owns serialized step persistence, parent selection and per-run read
ordering. The graph runner calls it before linking model usage and recording checkpoints.
See [ordering and legacy limits](../../../docs/observability-design.md#graph-step-ordering-limitation).

`mock_support_answer.py` owns bounded, explicitly labeled source excerpts for graph mock runs;
the graph owns orchestration. See the [mock contract](../../../docs/langgraph-workflow-design.md#mock-response-contract).

`answer_citations.py` owns answer-to-packed-source reference presence; `graph_routing.py` owns
deterministic routing under effective guardrail policies. Publication rechecks citation presence
before committing a final answer. Neither helper grades factual entailment.

`answer_duration_support.py` compares numeric durations in citation-free draft prose with only
the cited packed text returned by `answer_citations.py`. Routing and final guardrails share it;
see the [duration contract and limits](../../../docs/langgraph-workflow-design.md#numeric-duration-support).

Default `RetrievalService` uses lexical ranking with mock embeddings; traces expose that strategy
and null vector scores. Synthetic hashes never supply relevance to this path. Explicit vector
evaluation remains simulation until a semantic embedding provider is integrated and verified.

`retrieval_embeddings.py` owns vector validation and query embedding. RetrievalService marks
post-validation failures with a trace ID/outcome; the direct API or graph caller commits that
failure under its own transaction ownership. Trace reads enforce workspace knowledge permission.

`embedding_api.py` validates bounded OpenAI embedding requests/responses; `embedding_transport.py`
owns HTTP and sanitized errors. `embedding_runtime.py` selects the configured provider after
the API permission boundary; indexing and queries use the same model/dimensions settings.
See [the active integration plan](../../../docs/exec-plans/active/semantic-retrieval.md).

`accounted_embeddings.py` composes that API boundary with `embedding_attempts.py`. The latter owns
independent PostgreSQL admission/reconciliation transactions and pending/uncertain AIRun states.
It counts estimates until reported usage is known and preserves records on document rollback.
Each batch is admitted separately, with 64-chunk/64KB UTF-8 limits and validation before any call.
Graph query calls now carry run identity and per-run admission; `graph_retrieval.py` links ledger
attempts to the retrieval step and records failed tool/step output before review routing.
`knowledge_mutation.py` owns the transaction committing document changes and their audit.
The indexer uses it for successful publication; failed publication does not erase independently
committed provider usage. API actors are passed explicitly; internal reindex calls without an
actor record a system audit with null actor. See [verification](../../../docs/testing.md#knowledge-indexing-audit-publication).

`embedding_reconciliation.py` owns uncertain-usage confirmation and atomic audit persistence;
the Costs UI exposes confirmation; pending-call crash recovery remains open. `knowledge_indexing.py` owns indexing;
`knowledge_contracts.py` owns its result/error types. The knowledge service retains management.

| Domain | Owners | Main contract / focused design |
| --- | --- | --- |
| Identity and tenancy | `auth_service.py`, `workspace_service.py`, `folder_service.py` | Scoped users, roles, workspace/resource lifecycle; [security](../../../docs/security-threat-model.md) |
| Dataset ingestion | `dataset_service.py`, `import_parser.py` | Parse imports, examples/messages and labels; [database](../../../docs/database-schema.md) |
| Knowledge | `knowledge_service.py`, `document_parser.py`, `chunking.py`, `embedding_provider.py` | Version, chunk and index documents; [RAG](../../../docs/rag-design.md) |
| Retrieval | `retrieval_service.py`, `lexical_search.py` | Scoped ranking, citations and retrieval traces; [RAG](../../../docs/rag-design.md) |
| Agent execution | `agent_service.py`, `support_agent_graph.py`, `support_agent_state.py` | Run lifecycle, graph nodes, state and trace snapshots; [graph](../../../docs/langgraph-workflow-design.md) |
| Model and prompt boundary | `model_provider.py`, `model_config_service.py`, `prompt_runtime.py`, `prompt_template_service.py`, `support_prompts.py`, `langchain_support.py` | Provider calls, active prompt versions and prompt provenance |
| Budgets and usage | `model_call_planning.py`, `token_budget.py`, `token_accounting.py`, `budget_policy_service.py`, `ai_run_ledger.py` | Context estimates and ledger; [token economy](../../../docs/token-economy-design.md) |
| Governance | `guardrails.py`, `guardrail_catalog_service.py`, `human_review_service.py`, `tool_service.py` | Policies, review transitions and tool control; [tools](../../../docs/tool-execution-design.md) |
| Evaluation | `evaluation_loader.py`, `evaluation_runner.py`, `evaluation_metrics.py`, `evaluation_management.py` | Case execution, baselines, metrics and atomic management/audit transactions; [evaluation](../../../docs/evaluation-design.md) |
| Operations | `cost_service.py`, `attention_service.py`, `system_health_service.py`, `audit_log_service.py` | Scoped summaries and operator evidence; [observability](../../../docs/observability-design.md) |

## Dependency and persistence rules
`evaluation_execution.py` owns metric publication and unexpected-failure finalization around
case execution. It preserves committed accounting, emits content-free diagnostics and re-raises;
`evaluation_management.py` separately owns movement/archive/deletion and their audits.

`guardrail_catalog_stats.py` owns workspace-grouped usage and the newest eight failures per
guardrail type. Catalog rendering/filtering stays in `guardrail_catalog_service.py`. Catalog
reads use bounded query count rather than separate queries for every rule; this is not a
guaranteed refresh latency or a limit on the number of discovered rule types.

`agent_run_context.py` constructs the persisted GraphRun and initial graph state after
AgentService admission checks. Optional language is validated before creating the run.
`core/language.py` selects explicit EN/JA/ZH or automatic detection; the graph records selection
provenance. This extraction preserves existing commits and does not add crash recovery.

Services may use schemas/models, core primitives and focused collaborators. Do not import
HTTP routers or frontend code. Services currently use the SQLAlchemy session directly;
there is no complete repository abstraction. Introduce a helper when it clarifies transaction
ownership or eliminates actual duplication, not for every query by default.

Provider calls need attributable usage records. Graph and retrieval executions need traces.
Persist explicit failure states; do not hide an exception by returning a successful placeholder.
Keep workspace predicates at each data access boundary, even behind authorized routes.

## Priority corrections before production claims

- Budget display/context planning is not transactional spending admission.
- Stored checkpoints do not establish durable LangGraph resumption.
- Review mutations use `review_transaction.py` for row locking, refreshed state and a shared
  state/audit commit. PostgreSQL concurrency and rollback tests live in
  `backend/tests/test_review_transactions.py` (repository-relative path).
- `budgeted_model_provider.py` wraps graph and evaluation-baseline model dispatch with
  `budget_reservations.py` admission/reconciliation; `openai_transport.py` sends output caps.
  `evaluation_direct_baseline.py` and `evaluation_rag_baseline.py` own baseline generation.
  See [token limits](../../../docs/token-economy-design.md) for per-run and monthly scope.
- `graph_outcome.py` owns final guardrail/run/review publication. Node tracing and model ledger
  writes remain durable during graph execution; only final outcome publication shares this commit.
- Retrieval scores candidates in Python; default mock-provider searches use lexical relevance.
  Explicit vector evaluation still uses synthetic vectors and does not prove semantic quality.
- Evidence presence does not prove an answer is grounded; evaluation needs controlled baselines.

Each correction is a focused ticket with a failing regression test and evidence in the
[improvement loop](../../../docs/production-improvement-loop.md).
