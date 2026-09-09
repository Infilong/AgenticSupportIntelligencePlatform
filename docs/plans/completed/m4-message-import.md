# Bounded customer-message import

User outcome: DATA/UX — import labelled customer messages, inspect saved originals, and explicitly
start one selected message through the existing graph, evidence and review workflow.
Complexity: deep (atomic imports and the inbox's no-run projection); one implementation owner.

Scope: operator/admin JSONL upload, 1 MiB and 100 records per batch, original/language/labels fields;
all-or-nothing validation, replay-safe batch key, existing 50000-message cap. Imported content is
customer data, never knowledge. Viewers may inspect; only operators/admins import, label or start.
Start processing reuses initial run admission and remains safe under concurrent clicks.
Keep archived data, providers and RAG defaults unchanged. No paid calls or bulk auto-processing.

Implementation: conversations module owns import/labels; support retains Message and run ownership.
Add bounded batch metadata and optional batch reference/labels, scoped message detail, unprocessed
inbox filter, and nullable run links. Preserve existing run filter performance and URL navigation.
Frontend offers Import beside New message, then saved-message detail with a clear Start processing.
Relevant guides: root, backend, support, frontend, docs and infrastructure before runtime migration.

Verification: real PostgreSQL import/replay/conflict/rollback/limits/workspace and viewer denial;
concurrent first-start produces one job; existing inbox/support tests. Generated API, frontend
checks/build, real import → filter → inspect → label → start → Workflow browser journey at
360/768/1440, plus visible failed import. Independent code/docs review before checkpoint.

Latest direction: RAG is sufficient for a demo; further tuning is deferred. Capacity experiment
files are preserved under `.artifacts/rag-hardening/deferred-capacity-20260909`; application and
tooling restored to committed f0b9f79 before this slice. Failed measurements remain preserved.


## Verification checkpoint

25 focused passes,46 backend units,141 full PostgreSQL passes,31 frontend tests/build pass.
Evidence paths are in STATUS. Two real browser journeys pass in30s; screenshots inspected.
Chrome independently completed one imported Japanese message through real retrieval, attributed
development answer and internal approval; no external send or paid call.
Independent review found casefold-length/character drift, Unicode line-separator parsing, and
a label-only empty-state error; repaired with regressions. No remaining high-severity findings.
Initial focused failure preserved:23 passes,1 assertion failure and2 test setup errors at
`.artifacts/m0/message-import-20260909T091357697605Z`. The old assertion intentionally excluded
runless messages; changed to require their visibility and absence from Processing. Huge parameter
IDs exceeded Windows environment limits; explicit short test IDs fix setup without reducing input.
Two new component checks initially failed because file change simulation did not satisfy native
file-input validity; direct form submission now tests retry/abort, while real browser verifies
file upload. Final input styling verification follows; no backend source change after141pass.

Final input styling/build and connected browser journey pass at `.artifacts/m4/message-import-browser-final-20260909`; final screenshot inspected. Full backend regression predates only frontend styling and documentation.
