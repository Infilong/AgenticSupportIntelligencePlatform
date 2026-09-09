# Historical evaluation records

Read backend/AGENTS.md and evals/AGENTS.md. This module registers completed local retrieval
comparison evidence; it does not execute evaluations or supply answers to application workflows.
Never store or serve the raw multi-workspace report. Bind every case/probe trace to the report's
primary workspace before persistence. Registration requires its administrator under the workspace
lock; reads require current membership. Preserve immutable hashes, failed cases, denominators and
unknown generation quality. Report identity and arithmetic checks do not prove semantic quality.
Use real PostgreSQL tests for registration, isolation, revocation and idempotency.
