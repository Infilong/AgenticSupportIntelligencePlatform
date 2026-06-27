# Token Economy Design

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
- Real model providers remain postponed until the ledger, budget planner, and tests are stable.
