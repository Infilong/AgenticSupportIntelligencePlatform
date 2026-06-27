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
