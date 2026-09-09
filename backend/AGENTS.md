# Backend guidance

Scope: this directory and its descendants. Read the [root director](../AGENTS.md).
See [STATUS](../docs/STATUS.md) for progress and [architecture](../docs/ARCHITECTURE.md)
for implemented modules. This guide owns backend rules, not a duplicate milestone summary.

## Ownership

- Follow [architecture](../docs/ARCHITECTURE.md) and the backend topology in
  [release plan](../REBUILD_PLAN.md). Backend owns auth, permissions, persistence and accounting.
- Keep routes, validation, domain services, authorization, repositories and tests distinct.
  Routes, graph nodes and worker handlers call shared domain services.
- Scope workspace data before reads/writes, retrieval, tools, previews and model context.
  Queue payloads, documents and customer messages cannot grant authority.
- Coordinate API contract changes with [frontend guidance](../frontend/AGENTS.md).
- For customer imports and labels, read [conversations guidance](app/modules/conversations/AGENTS.md).
- For messages, runs and development handoffs, read [support guidance](app/modules/support/AGENTS.md).
- For attributable human decisions and final responses, read [review guidance](app/modules/reviews/AGENTS.md).

## Persistence and execution

- PostgreSQL owns business records/jobs; LangGraph checkpoints own workflow continuation.
- Commit a job and its business record atomically. Use bounded retries and fenced claims;
  replay/resume must not duplicate published results or human decisions.
- Do not hold database transactions open while awaiting providers. Preserve uncertain
  outcomes after crashes instead of reporting invented success or zero cost.
- Maintain original inputs, versioned evidence, attempts, reviewed results and decision history.
- Prefer maintained provider integrations and graph persistence over custom HTTP clients.
- Record model calls and retrieval/graph traces, including errors, durations, usage and cost.
- Retrieve/filter/compress before model calls. Keep clarification, missing/conflicting
  evidence, human review and technical failure distinct. Never use evaluation answers as runtime data.

## Verification

- Select relevant gates in [acceptance](../docs/ACCEPTANCE.md); cover successful, failing
  and permission-denied paths. Use real PostgreSQL for vector, isolation and concurrency tests.
- Fake only external AI providers in offline application journeys. Follow
  [evaluation guidance](../evals/AGENTS.md) for live quality claims.
- Add executable setup/test commands to [runbook](../docs/RUNBOOK.md) as implemented;
  `python scripts/manage.py verify-backend` runs current tests. Never validate against the archived runtime.
