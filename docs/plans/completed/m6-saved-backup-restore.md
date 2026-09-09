# Verify restoration from a saved local backup

## Execution brief

RESTORE: complete the operator backup/recovery loop by consuming a previously saved standalone
backup. Deep because database restoration executes SQL; root owns implementation, bounded
independent safety and semantic reviews required. Root/scripts/infra/backend/docs guides apply.
Existing authority covers disposable local databases; never overwrite or drop existing data.

Add optional `verify-restore --backup-dir .artifacts/m6/backup-<timestamp>`; preserve the default
fresh-snapshot drill. Keep archive validation/copying in a cohesive helper; the existing drill
owns clone creation, parity and new-request proof. Only trusted operator-created local backups
are supported. Resolve the directory and both files beneath the actual workspace artifact root.
Validate the successful standalone-backup manifest, expected source, bounded archive size and
fingerprints. Copy to an exclusively created evidence directory and verify the copy before any
database creation. Restore only that copy; never re-export today's source in saved-backup mode.

Verify valid/invalid manifests, missing/corrupt/escaping files, copy mismatch, no source export
and preserved default mode. Real proof uses an older saved backup after a new synthetic source
request, compares clone state to the saved fingerprints, and processes a fresh clone request.
Keep original archive/hash and existing source records unchanged. No recovery-time SLA, generic
remote restore, migration conversion, cloud or automatic retention. Stop at14:58 UTC.

## Trust and design

Independent design review requires copy-before-createdb, complete early validation, stored rather
than current fingerprints, retained failed targets, and no false provenance claims. A checksum
detects corruption relative to the manifest; it does not authenticate an attacker-controlled pair.
[PostgreSQL documents](https://www.postgresql.org/docs/current/app-pgrestore.html) that restoration
executes code selected by the source superuser. This is an operator command for trusted backups,
not an application endpoint accepting uploaded archives. No restore of untrusted material occurs.

## Verification and repairs

Seven focused archive tests and six backup/restore boundary tests pass. Initial lint found one
112-character test line and an unused helper import; both are repaired and final checks pass.
One generation command initially ran from backend rather than repository root; the corrected
root command generated the source reference. No application behavior changed for these repairs.
All71 backend units pass at `.artifacts/m0/backend-20260909T141032167323Z`, with the existing
AnyIO deprecation warning retained. Backup checkpoint338a88c's CI34360979852 passed.

The actual development source processed synthetic request
`d9029f28-c1fd-485f-a52c-d8c0b2236de0` after the retained13:57 backup. Saved restore passes at
`.artifacts/m6/restore-saved-20260909T141055Z`, wrapper
`.artifacts/m0/restore-20260909T141054354160Z`. All23 tables and metadata match the old manifest.
Clone `asi_restore_eb95583880c6` processes new request `88239c3a-2e2f-47f1-9e49-7ef95045c2bb`
to clarification with three checkpoints and no model calls. No active inherited jobs existed.

Separate verification at `.artifacts/m6/saved-backup-proof-20260909/verification.json` confirms
the newer source message remains in source and is absent from clone, the new clone message is
absent from source, and original backup/manifest hashes are unchanged. The first supplementary
SQL query incorrectly named messages instead of support_messages; it failed read-only. After
checking the real model/table name, the corrected four existence checks pass.

The unchanged default option also passes a real fresh-snapshot regression at
`.artifacts/m6/restore-20260909T141337Z`, wrapper `.artifacts/m0/restore-20260909T141335199353Z`:
23-table parity and new clarification in clone `asi_restore_4ff21e112262`. These are API/worker
checks, not restored browser/network deployment or generation quality. All clones are retained.

Independent safety and semantic-documentation reviews closed with no actionable findings.
All53 preparation checks pass at .artifacts/m0/prep-20260909T141735149948Z. This completion
note follows verification and changes no runtime or mapped documentation contract.
