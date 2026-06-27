# Milestone 6: AI Run Ledger And Token Budget Planner

## What Was Built
Milestone 6 added the token-economy and observability foundation:
- `ModelConfig`, `PromptTemplate`, `AIRun`, and `CacheEntry` tables.
- deterministic token estimation and cost estimation utilities.
- `TokenBudgetPlanner` for model choice, compression, cache, denial, and human-review routing decisions.
- `MockModelProvider` that records every success and failure as an `AIRun`.
- workspace-scoped cost summary API.
- tests for accounting, budget decisions, failed runs, cache uniqueness, and workspace isolation.

## Why Companies Care
Production LLM systems need margin control, latency control, debuggability, and incident analysis. A run ledger answers: which model was called, why, how many tokens were used, what it cost, whether cache helped, how long it took, and whether it failed.

## How This Project Uses It
Future LangGraph nodes will call model providers through ledger-aware wrappers. Each model call can attach to graph run and graph step IDs once Milestone 7 adds them. The cost summary endpoint already lets a workspace inspect aggregate AI usage.

## Design Tradeoffs
- Pricing is estimated and configured for demo/mock models; it is not billing-grade.
- The mock provider records real database rows but never calls an external model.
- Existing embedding paths are not fully retrofitted yet, keeping this milestone focused on the ledger contract.
- Token estimation is deterministic and approximate; exact provider tokenizers can be introduced behind the same API later.

## Failure Modes
- If future code bypasses the provider wrapper, model calls may not be recorded.
- Cost summaries must always filter by `workspace_id`.
- Cache values can contain sensitive content, so future UI/logging must avoid leaking raw payloads.
- Incorrect pricing can mislead stakeholders; label costs as estimates.
- Token planners that only deny requests can hurt UX; human-review routing is a better fallback for high-value cases.

## Interview Explanation
“I built an AI run ledger before adding agent workflows. Every mock model call records provider, model, purpose, language, token counts, estimated cost, latency, cache status, success/failure, and optional prompt version. The token budget planner makes deterministic pre-call decisions: cheaper model for classification, compression for large context, denial for token overflow, and human-review routing for high estimated cost. This is how I would protect cost, latency, and observability in a production LLM system.”

## Review Checklist
- Verify all cost summaries are workspace-scoped.
- Verify failed provider calls still create `AIRun` records.
- Verify budget decisions happen before model calls.
- Verify no real provider is used in tests.
- Verify pricing is documented as estimated.
