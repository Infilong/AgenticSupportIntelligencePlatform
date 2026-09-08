# Evaluation fixtures

All data here is synthetic. `fixtures/manifest.json` declares document identity, language,
version and active status. `cases/m0.json` contains 15 initial cases: five each in EN/JA/ZH.
The English incident policy deliberately supports Japanese and Chinese questions. An archived
30-day policy must be excluded from new retrieval; current policy says 14 days.

These are source-supported expected facts and outcomes, not model answers. Application code
must never read this case file to generate a response. A test runner will consume it in M2/M5.
No retrieval or model-quality evaluation has run yet. M0 checks only fixture consistency.

The source list identifies required evidence, not an exhaustive ban on equivalent translated
policy citations. Final scoring must recognize equivalent active translations while requiring
every policy claim to be supported. Historical and foreign-workspace evidence is never valid.
Missing-evidence cases may retrieve unrelated passages; they still must not invent an answer.

Before tuning: expand to at least ten cases per language and a coherent 30–50-page equivalent
policy corpus; add genuine active conflicts, boundary days, renewals, and withdrawn evidence.
Freeze thresholds, denominators and source-equivalence mapping in ACCEPTANCE.md before live tuning.
Model grading is auxiliary. Keep representative answers for human support/citation review.
