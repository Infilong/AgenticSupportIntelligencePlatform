# Cost Workbench Filtering

## Goal
Make the token/cost dashboard easier to operate when a workspace has many agents, model routes, graph runs, and AI ledger rows.

## Context
Token economy is a first-class project requirement. The backend already records and summarizes model calls, latency, cost, cache hit, failures, graph runs, and agent/model/purpose attribution. The frontend showed the data, but investigation controls were limited: operators could not search across spend drivers or filter graph-run and AI-ledger status from one place.

## Requirements
- Add a cost investigation search input shared across spend driver cards, recent graph-run spend, and AI ledger rows.
- Add graph-run status filtering for recent graph-run spend.
- Add AI-call status filtering for recent ledger rows.
- Bound spend driver cards and show clear visible/matching counts.
- Preserve trace drilldown from graph-run spend rows.
- Do not change backend cost accounting in this ticket.

## Non-goals
- Do not add backend pagination.
- Do not change token/cost formulas.
- Do not change budget enforcement.

## Test Plan
- Run frontend production build.
- Run `git diff --check`.

## Human Review Checklist
- Confirm cost search can find agents, models, purposes, routes, and ledger rows.
- Confirm failed runs and failed model calls are easy to isolate.
- Confirm the dashboard still foregrounds token budget and model-call cost signals.

## Interview Notes
This improves operational observability: a production AI platform should not only record cost, it should let engineers investigate which agent, purpose, model, or failed run is consuming budget or causing latency.
