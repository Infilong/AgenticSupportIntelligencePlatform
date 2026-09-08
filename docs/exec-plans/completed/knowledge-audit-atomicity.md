# Knowledge mutation audit atomicity
## Goal
Prevent document mutation success from persisting without its attributable audit record.
## Context
Routes currently audit after service commits. Move/delete are ordinary database transactions;
upload/reindex also preserve indexing failure state and independent embedding usage records.
## Requirements
Atomic mutation/audit publication, explicit rollback, real actor attribution, retained permission
checks and independently durable provider accounting.
## Non-goals
Durable job recovery, replay after ambiguous commit acknowledgments, changing role permissions.
## Acceptance Criteria
Move/delete failures leave document/index/audit unchanged and permit retry; PostgreSQL observers
cannot see mutation before audit commit. Upload/reindex publication and failure accounting must
also receive a separately verified repair before this plan is complete.
## Plan
1. Reproduce move/delete audit failure using API calls and indexed data.
2. Add a focused mutation commit helper; services own actor/audit, routes retain permissions.
3. Verify rollback and separate-connection PostgreSQL visibility, then browser integration.
4. Inspect and repair upload/reindex final publication without erasing failed provider usage.
## Verification
Failure injection, permission regression, PostgreSQL visibility, relevant browser checks and lint.
## Risks
Deleting index relationships must roll back too. Indexing exceptions intentionally persist failed
status; treating indexing as ordinary rollback could erase useful recovery state or usage.
## Progress
2026-09-08 inspected service/indexer/audit and independent embedding ledger transactions.
Implementing steps 1-3 before changing the indexing publication contract.
Steps 1-3 complete: two API tests reproduced persisted moves/deletes after audit failure
(`.artifacts/knowledge-audit/before.log`). Services now require the acting user and use
`knowledge_mutation.py` to flush mutation, stage audit and commit together, rolling back on
failure. Route permissions are unchanged; duplicate route audits were removed for move/delete.
Ruff and 37 affected tests pass in 18.40s, including two separate-connection PostgreSQL tests.
The initial lint failure is retained in `backend.log`; accepted run is `backend-corrected.log`.
Rebuilt API with mock providers: four browser checks pass in 29.6s, including full EN/JA/ZH
journeys. Runtime contains 543 HTTP outcomes with zero server/error outcomes. Source-size gate
passes over 165 application files. No unresolved P0/P1 finding in the move/delete repair.
Next: step 4 must pass actor attribution into indexing final publication, stage its success
audit before commit, and preserve existing failed-status and independent usage persistence.
Reproduce upload/reindex audit failure first; add provider-failure and PostgreSQL checks.
## Decisions
2026-09-08 indexing publication completed: upload/reindex audit failure reproduced twice in
`index-before.log`. Success audit now stages inside the indexer's final commit, outside its
provider-failure handler; rollback restores prior publication state while the independent
embedding ledger retains spent usage. API calls pass the authenticated actor. Direct internal
reindex calls may omit the actor and produce an unattributed system audit, rather than falsely
attributing the operation to the original uploader.
Ruff and 45 affected tests pass in 28.83s (`index-backend-corrected.log`), including PostgreSQL
observer/usage/retry checks and existing provider-failure tests. A test formatting failure is
retained in `index-backend.log`. Twelve browser checks pass in 35.1s after rebuilding the API;
1,238 HTTP outcomes have zero server/error outcomes. Providers are mocks/synthetic transports.
Source-size and documentation gates and whitespace checks pass. Final review found no unresolved
P0/P1 in the scoped transaction repair. Original failure logs and intermediate history remain.

Keep the commit helper separate to preserve the existing service's sub-300-line boundary.
## Findings
Move/delete commit before route audit; provider accounting uses separate sessions.
## Final Result
Completed 2026-09-08: management and successful indexing publication now commit with their audit.
Failure injection, PostgreSQL visibility and retained provider usage meet the scoped criteria.
Failed indexing still persists explicit failed status; this is not durable crash recovery,
automatic replay, uncertain-commit resolution or proof of concurrent reindex serialization.
