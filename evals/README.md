# Evaluation fixtures

All data here is synthetic. `fixtures/manifest.json` declares document identity, language,
version and active status. `cases/m0.json` contains 15 initial cases: five each in EN/JA/ZH.
The English incident policy deliberately supports Japanese and Chinese questions. An archived
30-day policy must be excluded from new retrieval; current policy says 14 days.

These are source-supported expected facts and outcomes, not model answers. Application code
must never read this case file to generate a response. A test runner will consume it in M2/M5.
M0 checks prove fixture consistency only. Real retrieval measurements are now recorded in
[current status](../docs/STATUS.md); generation quality remains a separate acceptance gate.

The source list identifies required evidence, not an exhaustive ban on equivalent translated
policy citations. Final scoring must recognize equivalent active translations while requiring
every policy claim to be supported. Historical and foreign-workspace evidence is never valid.
Missing-evidence cases may retrieve unrelated passages; they still must not invent an answer.

Before tuning: expand to at least ten cases per language and a coherent 30–50-page equivalent
policy corpus; add genuine active conflicts, boundary days, renewals, and withdrawn evidence.
Freeze thresholds, denominators and source-equivalence mapping in ACCEPTANCE.md before live tuning.
Model grading is auxiliary. Keep representative answers for human support/citation review.

## M2 frozen corpus

The expanded [v1 corpus and scoring protocol](corpus/v1/README.md) now contains two substantial
company manuals, selected Japanese/Chinese translations, historical/withdrawn/foreign sources
and an active policy conflict. It totals 81,502 bytes and 38.2 page equivalents under the
recorded convention. Thirty fixed cases and factual spans are independent evaluator inputs.
Run `python evals/freeze_retrieval.py` to check its frozen hashes. Initial review snapshots are
retained separately; all strengthening occurred before the first retrieval measurement.
See [current status](../docs/STATUS.md) for actual retrieval evidence and its limitations;
corpus size alone is not a quality result.

The September 9 audit tightened the evaluator under scorer version
`active-required-sections-v2`: factual spans count only in active top-five passages from
required sections, and negative probes must respect result limits. Corpus v1 inputs and
historical reports remain unchanged. This is still section-scoped substring evidence, not
per-claim source entailment. Source/version-bound judgments and forced cross-language cases
need a separately frozen corpus version; see [RAG design](../docs/RAG.md).
