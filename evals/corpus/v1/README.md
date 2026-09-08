# Frozen retrieval evaluation v1

All sources are synthetic. Paths in `manifest.json` are relative to `evals`. The two substantial
English manuals cover customer and service operations; Japanese and Chinese sources cover
selected equivalent policies. This is not a full translation of every long English chapter.
Cross-language cases deliberately require evidence whose language differs from the query.

Page-equivalent convention, fixed before retrieval measurement: 300 English-style word tokens
or 900 CJK characters per page, reflecting readable policy pages with headings. Count readable
source text, not JSON, and report actual bytes/words/characters alongside the equivalent.
The target is 30–50 equivalents across the corpus; it is not a claim about rendered PDF pages.

`cases/retrieval-v1.json` contains ten fixed cases per language. Each nonempty `groups` entry
requires at least one returned section from that equivalence group in the first five results.
Matching section IDs across active translations/handbooks are equivalent evidence. All groups
must be met for a case to pass; the trial conflict deliberately requires both active sources.
Only active primary-workspace versions are eligible, regardless of matching section labels.

Section matches are discovery evidence only. `cases/retrieval-facts-v1.json` additionally
requires at least one normalized factual span from every listed alternative group in the
returned passages. Case success@5 requires both section discovery and factual coverage.
This catches, for example, the short incident reporting section missing its separate
do-not-wait boundary. Exact span checks supplement, not replace, human semantic review.
The required-evidence case denominators are EN 8, JA 9, ZH 9 (26 total); evidence-section
group recall has denominators EN 8, JA 10, ZH 9 (27 total). Report both metrics. Both must
meet the original >=90% overall / >=80% per-language targets; this strengthens the gate.
Case minima are 24/26 overall, 7/8 EN, 8/9 JA and 8/9 ZH, without rounding percentages.

Hashes and source-byte counts use UTF-8 with LF line endings so Windows/Linux checkouts
share the same evaluation content fingerprint; uploaded originals retain their actual bytes.
Freeze source files, manifest and cases with SHA-256 before tuning. Pass targets remain
recall@5 >= 90% overall and >= 80% for each language among cases with required evidence;
zero withdrawn/superseded/foreign-source leakage; warm single-user p95 <= 3 seconds.
Report all ten cases per language, plus the answerable denominators used for recall.
Empty groups are clarification/insufficient-evidence routing cases: record retrieval candidates,
but do not pretend candidate retrieval verifies the expected generation/workflow outcome.

Latency: one discarded warm-up using the first fixed question, then one timed HTTP request
per case in file order, one concurrent client. Include session validation, query embedding,
database search and response transfer. Use nearest-rank p95 (ceil(0.95*n)), not interpolation.
Cold ingestion is measured separately. No repeated timing selection or discarded slow cases.
Additional mandatory probes target the withdrawn fifteen-minute lunar offer and foreign
365-day refunds/99-day exports, plus an unauthorized request to the foreign workspace.
They test leakage and do not change the 30-case quality denominators.

The trial circular is a genuine active conflict with the handbook's extension limit. The old
refund version is replaced through the real upload API, the retired offer is withdrawn through
the API, and the private agreement belongs to a separate evaluation workspace. Expected cases
and equivalence groups are consumed only by the evaluator, never the application.
