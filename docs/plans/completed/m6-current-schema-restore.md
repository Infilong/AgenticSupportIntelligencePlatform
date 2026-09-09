# Current-schema recovery verification

## Execution brief

RESTORE/TENANT: refresh recovery proof after historical evaluations introduced migration0014.
Normal bounded verification, root owner. Read root/scripts/infra/backend/evaluation guides.
Reuse the existing restore drill: read-only exported snapshot, fresh uniquely named database,
all-table fingerprint/metadata parity before mutations, new authenticated clarification through
ASGI and real worker. Never overwrite/drop databases or resume inherited jobs.

Then inspect the restored evaluation record through authenticated application APIs, using
synthetic accounts and the stored workspace/record identities. Compare the restored API projection
with the clone's stored row; source-snapshot equivalence comes from preceding table-hash parity.
Verify foreign workspace denial, preserve metadata and exact evidence. No claim
of network/browser restore deployment, restored generation/RAG quality or native zoom.
No app/schema changes unless an actual recovery defect is found. Existing generation/provider
and zoom limits remain. Independently review saved recovery evidence and update owning docs;
close the successful release CI record, commit/push and continue within14:58 UTC.

## Evidence

Passed: `.artifacts/m6/restore-20260909T132319Z/report.json`; command/source evidence
`.artifacts/m0/restore-20260909T132317840990Z` (25.36s, source unchanged during execution).
All23 public tables and extension metadata match the same exported backup snapshot; no sequences.
The4,093,256-byte dump and disposable clone `asi_restore_7549ecc140ed` are retained. One historical
evaluation record is included. No inherited queued/running jobs existed, so quarantine is unexercised.
New ASGI/worker request51c0c84d-281a-4cfc-b6e9-b8161770076e completed as clarification_needed,
job succeeded, three checkpoints, zero model calls.

Supplementary `verify_evaluation.py`, `evaluation-api.json` and `evaluation-api.log` in the same
restore directory pass. Only the new clone is accessed: anonymous list/detail401, foreign
list/detail404, admin list/detail200, exact API snapshot equality with its database row, five
strategies/150 cases, retained ja02 failed comparison and actual succeeded retrieval trace.
The foreign account cannot read that trace(404). The unchanged historical report hash is
e7aec139381623da03adceee99f74cb79470123f039fd3476530b6638681292b.
Login creates clone sessions; this supplementary check is not a read-only transaction as a whole.

Independent review verified table/hash parity, dump hash and the supplementary results. Corrected
wording to distinguish clone API-versus-row equality from source-snapshot parity; it does not
compare current source API responses. No product defect found and no product/schema code changed.
Network/browser restore deployment, restored generation/RAG quality and native zoom remain
unverified. Latest hosted CI34355803730 passes all five jobs at revisionf1a64dc; release build,
seed, browser and cleanup steps executed successfully, failure diagnostics correctly skipped.
The README still said restoration was unimplemented; corrected it to the actual verify-restore
and packaged-release commands while retaining separate backup/live-generation gaps.
Independent semantic review passed and renewed the three affected receipts. First preparation
run `.artifacts/m0/prep-20260909T133136915137Z` passed45 checks and failed the tracked-document
inventory check because the completed CI plan's move was not yet staged. Stage that exact rename
before rerunning; no assertion or document requirement is relaxed.
With the exact rename staged,46 preparation checks pass in11.383s at
`.artifacts/m0/prep-20260909T133241541823Z`; freshness check passes. This completion note follows
that run; product source and reviewed owning-document content are unchanged.
