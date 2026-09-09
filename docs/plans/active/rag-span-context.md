# RAG source spans and context retention

## Execution brief

User outcome: trustworthy source inspection and retention of usable ranked evidence (RAG,
TRACE, TENANT). Continue M1–M6 within the existing 06:04:24–10:04:24 UTC window on September 9.
Base `15e3218`; no paid API, deployment, merge, schema changes or archived-data rewrites.

Independent review reproduced two P2 defects: matching repetitive chunk text with `find`
can assign an earlier occurrence, while `rfind` carries a different occurrence; context packing
stops at the first oversized source even when a later selected source would fit.

This is a deep provenance repair. Root owns implementation. Read root/backend/support/docs
guides and docs/RAG.md. Track positions during recursive partitioning, retaining LangChain's
token-aware merge/overlap behavior; never infer location from an ambiguous text match. Keep the
350/45 recipe, section boundaries, bounded work, cancellation and 1,000-chunk cap. Put the span
adapter in its own cohesive module. Keep at most the existing top-five candidate policy and
24,000-byte transport bound; skip oversized complete snapshots and consider later candidates.
This does not supply a model-token budget or semantic citation validation.

Verification: reproduce both failures first; known-position repetitive EN/CJK and whitespace
fixtures, coverage through artificial boundaries, vanilla LangChain text compatibility,
existing chunk/cancellation/cap regressions, exact/over/all-source context budgets. Run backend
unit and relevant real PostgreSQL regressions, fresh local retrieval corpus/boundary probes,
inspect affected source UI, obtain independent review, update docs and checkpoint to the branch.
Existing stored chunks remain immutable; new versioned ingestion receives the repair.

Completion: passing unchanged criteria, reviewed provenance behavior and honest evidence;
then select the next dependency-ready release gap without expanding the authorized scope.

## Repair evidence so far

Four expected failures reproduced before implementation in `.artifacts/rag-hardening/span-before2.xml`:
wrong repeated EN/CJK starts, lost document-tail coverage and skipped fitting context. The earlier
attempt also hit Windows' environment-variable length limit because a parameterized case used
its entire 8,000-character CJK string as its name; explicit short test IDs resolve that fixture issue.

SpanSplitter now partitions with sequential positions and reuses LangChain merging/joining.
Source carry uses its actual last span. Context checks later candidates after dropping an oversized
snapshot. Independent review found no blocking defect; added the requested word-token + special-token
overhead compatibility test. Existing sources/versions and permissions are unchanged.

Initial 38 units passed at `.artifacts/m0/backend-20260909T071540448254Z`; full PostgreSQL 116 passed
in 287.99s at `.artifacts/m0/integration-20260909T071621876300Z`. Real EN/JA/ZH boundary retrieval
passed at `.artifacts/rag-hardening/boundary-20260909T071922Z/report.json`. Final unit/corpus evidence
follows; no broader semantic claim is implied. Capacity checkpoint CI `34322603929` passed.

Final 39-unit pass: `.artifacts/m0/backend-20260909T072159482639Z`. Frozen real retrieval:
`.artifacts/m2/retrieval-eval-20260909T072217Z/report.json`, 26/26 evidence cases, 27/27 groups,
EN8/8, JA9/9, ZH9/9, warm p95 2.672s; four generation/routing cases remain unverified.
The corpus/thresholds stayed unchanged and all 30 queries ran. No semantic-quality or live-API
claim follows. Chrome showed the recorded workflow for the approved Japanese support example.
