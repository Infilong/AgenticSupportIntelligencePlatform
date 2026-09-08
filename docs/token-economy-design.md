# Token Economy Design

## Durable embedding attempts
The accounted embedding provider has an independent PostgreSQL ledger transaction. Before
dispatch, it serializes on the workspace using NO KEY UPDATE, checks monthly ledger plus active
graph reservations, and commits a pending AIRun using a conservative UTF-8 byte estimate.
Success replaces that estimate with reported usage; uncertain failures retain the estimate and
are explicitly marked uncertain. Monthly admission counts the attempt's creation month; estimates
are not automatically released, and historical unresolved attempts remain visible in the ledger.
No database lock spans provider I/O. Caller document transactions are never committed by the ledger.
Pricing is an explicit runtime configuration input; mock remains the default provider.
Graph query embeddings carry backend-owned run identity. Admission validates run/agent workspace
ownership and checks the agent token limit plus per-run token/cost policy against ledger usage
and active reservations. Pending query usage counts toward later graph calls. After retrieval,
the node links embedding attempts to its graph step; uncertain attempts retain their estimates.
Budget denial skips paid dispatch and routes the default workflow to human review. The operator
reconciliation API and Costs UI accept confirmed usage with an audit reference; pending-call
crash recovery and real-provider billing verification remain open.

## Goal
Token economy is a first-class product and engineering requirement. Companies care because model calls affect margin, latency, reliability, and user experience.

## TokenBudgetPlanner
Implement a `TokenBudgetPlanner` that decides:
- max retrieved chunks
- whether context compression is needed
- whether a cheaper model can be used
- whether cached results can be reused
- whether a request exceeds budget
- whether to route to human review due to high estimated cost

## Required Tracking
Track for every model call:
- prompt tokens
- completion tokens
- total tokens
- model
- provider
- purpose
- estimated cost
- latency
- cache hit
- language
- graph run
- graph step

## Cost-Saving Strategy
- deterministic code for parsing, routing, formatting, and validation where possible
- cheap/small models for classification, routing, and validation
- stronger models only for final generation or judgment
- embedding cache
- retrieval result cache
- compressed context cache
- repeated model output cache where safe
- strict context packing before generation

## Tests
Tests should prove:
- long documents are not sent raw to the LLM
- classification uses cheaper/smaller model config
- final answer respects token budget
- compression result can be cached
- cost is recorded for every AI run
- high-cost cases route to review when configured


## Implemented In Milestone 6
- `AIRun` ledger records provider, model, purpose, language, token counts, estimated cost, latency, cache hit, status, and errors.
- `MockModelProvider` records an `AIRun` for every successful or failed mock model call.
- `TokenBudgetPlanner` selects cheaper models for classification/routing, recommends compression for large contexts, denies over-token requests, and routes high-cost requests to human review.
- Cost summary API aggregates runs, tokens, estimated cost, latency, cache hit rate, and purpose breakdown per workspace.
- Cache entries are workspace-scoped and unique by workspace/cache key/purpose.

Known limitations:
- Pricing values are estimates for portfolio/demo behavior, not billing-grade provider prices.
- Existing embedding paths are not yet retrofitted into the AI run ledger; future provider wrappers should route through ledger-aware services.
- Configured OpenAI-compatible providers are supported; automated tests stub transport and make
  no paid calls. Pricing and prompt-token accounting remain estimates.


## Workspace Budget Policy
Workspace owners configure budget policy through backend-enforced settings, not UI-only hints. The policy includes monthly token budget, monthly cost budget, per-run token cap, per-run cost cap, hourly agent-run rate limit, and alert threshold. Cost summaries include current-month usage against the policy, and System Health reports warning status when budget usage crosses the configured alert threshold. Agent run creation enforces the hourly rate limit and the runtime uses the lower of the agent token budget and workspace per-run token cap.

## Agent model-call admission
Classification and drafting use `BudgetedModelProvider`. It commits a workspace-scoped reservation
before dispatch, counting current-run/month ledger usage and active reservations. Workspace row
locks serialize admission and reconciliation; no such lock spans provider I/O. Denial records
carry token/cost/monthly reasons, create no AI call and route the graph to review with a failed
step. Proactive model-context failures remain separate (`model_context_exceeded`) in graph traces.

Real calls reserve a conservative prompt allowance (UTF-8 bytes plus 32 for framing) and request
at most 512 completion tokens for classification or 1,024 for drafting. This allowance is not a
universal tokenizer guarantee. The transport uses
[`max_completion_tokens`](https://developers.openai.com/api/reference/resources/chat), which covers
visible output and reasoning tokens for supporting providers. Incompatible endpoints fail
explicitly; there is no retry that removes the cap. Model output exceeding its reservation routes
to review and retains actual ledger usage for subsequent admission.

Successful calls with complete nonnegative integer usage consume their reservation and link the
AI ledger. Known mock pre-ledger failures release it. Network errors, missing/partial usage and
unknown real dispatch outcomes retain allowance until explicit finalization/reconciliation.
The expiry timestamp is diagnostic metadata, not permission to release unknown usage, including
across monthly admission windows. Missing usage still has estimated ledger totals; it is
not authoritative billing. Finalization and admission share a workspace lock; an in-flight ledger
plus active reservation can temporarily count conservatively twice, but consumed reservations
are not counted twice. Abandoned reservations can block spending; ownership-based recovery
is still open in the [recovery plan](exec-plans/active/interrupted-call-recovery.md). Never
manually release an unknown dispatched call merely because its timestamp expired.

This policy governs agent classification/drafting, including `system_v1` evaluation runs, and
direct/vector-RAG baseline generation. Baseline reservations belong to an evaluation run instead
of a synthetic graph. Its direct/vector model calls share the workspace per-run token/cost limits
across cases and modes; graph calls retain their own graph/agent limits. All share monthly ledger
and active-reservation admission. There is no combined system-v1/baseline evaluation-batch cap.
RAG embedding admission remains a separate workspace mechanism described above.

Budget denial produces an evaluation result with route `error`, the specific denial reason,
no answer and zero model prompt tokens; it does not dispatch a model. Successful baseline usage
links through its consumed reservation to the AI ledger. Evaluation deletion locks the workspace
and rejects all unresolved reserved rows with 409, including expired rows, so deletion cannot
erase their allowance or evidence.
Migration 0030 enforces exactly one graph/evaluation owner and preserves old graph reservations;
downgrade refuses while any evaluation reservations exist, including completed history.
Exact external billing, rate-limit concurrency, live pricing validation and crash-safe retries
remain separate work.
