# Run-Level Token And Cost Budget Reservations

## Goal

Enforce model context, agent token, workspace per-run token/cost, and workspace monthly token/cost limits before every model invocation.

## Context

The current planner estimates a single call against the selected model context window. `AgentService` computes an effective token budget but the graph does not consume it. Workspace per-run cost and monthly budgets are displayed but not in the execution path. Classification and drafting are the current model-call sites.

## Requirements

- Reserve estimated tokens and cost before each model call.
- Count completed AI-run usage plus non-expired active reservations.
- Enforce the minimum of agent token budget and workspace per-run token budget.
- Enforce workspace per-run cost and monthly token/cost budgets.
- Keep model context enforcement distinct from product budget enforcement.
- Persist denial reason as one of:
  - `model_context_exceeded`
  - `token_budget_exceeded`
  - `cost_budget_exceeded`
  - `monthly_token_budget_exceeded`
  - `monthly_cost_budget_exceeded`
- Route every denial to human review without invoking the model provider.
- Finalize a reservation with actual AI-run usage on success or provider failure.
- Release a reservation on an unexpected pre-ledger exception.
- Expire abandoned reservations so a crashed worker cannot block a workspace forever.
- Keep every query scoped by `workspace_id` and `graph_run_id`.

## Non-goals

- Provider-side prepaid credit management.
- Exact billing reconciliation beyond recorded provider usage.
- Distributed rate limiting.
- Redis-based reservations.
- Retrofitting non-agent evaluation calls in this ticket.

## Design Plan

### Persistence

Add `ModelCallReservation`:

- `id`
- `workspace_id`
- `graph_run_id`
- `ai_run_id nullable`
- `purpose`
- `estimated_tokens`
- `estimated_cost`
- `status: reserved / consumed / released`
- `denial_reason nullable`
- `expires_at`
- `created_at`
- `finalized_at nullable`

Only `reserved` rows with `expires_at > now` count as outstanding usage. `consumed` rows are represented by their linked `AIRun` and are not counted twice.

### Reservation Transaction

1. Resolve model pricing and estimate the call.
2. Reject calls larger than the model context.
3. Lock the workspace budget-policy row where supported.
4. Sum current-month `AIRun` usage and active reservations.
5. Sum current-run `AIRun` usage and active reservations.
6. Check agent/per-run token, per-run cost, monthly token, and monthly cost limits.
7. Insert and commit a reservation before provider invocation.
8. Invoke the provider.
9. Finalize the reservation with `ai_run_id`, actual usage, and `consumed`.
10. Release on an unexpected exception that did not create an AI run.

### Runtime Integration

- `AgentService` keeps passing the effective run token limit.
- A focused reservation service owns queries and transactions.
- The model-call planning module owns model context estimates.
- Classification and drafting nodes reserve before their LangChain chain runs.
- Budget denial updates graph state and persists a failed graph step.
- Existing guardrails and human-review routing consume the explicit reason.

## Files Likely To Change

- New budget reservation model and Alembic migration.
- New reservation service.
- Token budget decision types.
- Support agent state.
- Classification and drafting call sites.
- Trace/response schema only if reservation evidence is exposed.
- Focused unit and API integration tests.
- Database and token-economy docs.

## Test Plan

- Model context denial makes zero provider calls.
- Agent token-budget denial makes zero provider calls.
- Workspace per-run token denial makes zero provider calls.
- Workspace per-run cost denial makes zero provider calls.
- Monthly token denial includes prior AI-run usage.
- Monthly cost denial includes prior AI-run usage.
- Active reservations prevent a second run from overspending the same remaining budget.
- Expired reservations do not block a call.
- Successful calls consume and link reservations.
- Failed provider calls consume and link reservations to failed AI runs.
- Unexpected pre-ledger failures release reservations.
- Classification plus drafting share one run budget.
- Cross-workspace usage and reservations never affect another workspace.
- Full backend suite and Ruff pass.

## Risks

- Holding a database lock during a network call would reduce throughput; the design commits the reservation before invoking the provider.
- A crash after the provider responds but before finalization can temporarily over-reserve; expiration bounds the impact.
- Retrying a graph node must not create duplicate active reservations for the same logical attempt.
- SQLite ignores row locks, so concurrency correctness needs a PostgreSQL integration test.
- Estimated usage may differ from provider usage; finalization records actual usage and subsequent calls use actual totals.

## Acceptance Criteria

- Every agent model call has an allowed reservation or an explicit denial before provider invocation.
- No denied call creates an `AIRun`.
- Two calls in one graph share the same run limits.
- Monthly and per-run cost limits affect runtime, not only dashboards.
- Reservation and AI-run records are workspace scoped and auditable.
- No new source file exceeds 300 lines.
- No existing oversized file grows overall.
- Focused tests, full backend tests, Ruff, Alembic head, and PostgreSQL reservation tests pass.

## Human Review Checklist

- Verify consumed reservations are not double-counted with AI runs.
- Verify all denial paths route to review with a specific reason.
- Verify reservations are created before provider calls.
- Verify transaction boundaries do not hold locks during network I/O.
- Verify expired reservations are ignored.
- Verify workspace and graph-run filters are present on every aggregate.

## Interview Notes

- Explain reservation-based quota enforcement versus after-the-fact observability.
- Explain why estimates are reserved before calls and reconciled to actual usage afterward.
- Explain the crash-recovery tradeoff of expiring reservations.
- Explain why PostgreSQL row locking matters even though local SQLite tests pass.
