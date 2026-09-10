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


## Five-strategy retrieval comparison

Run `uv run --project backend --frozen python evals/compare_retrieval.py` after the local stack is
healthy and source-matched. It ingests one fresh frozen corpus, warms each strategy, rotates
strategy order per case, and times only the retrieval POST. Trace fetches and report writes are
outside the latency sample. All 30 requests per strategy remain visible; four outcome-only cases
are generation/routing-unverified. Candidate section-group discovery at 20/40 is separate from
final 5 required factual spans. No evaluator facts or expected sections reach application inputs.

The command exits 0 for a complete source/runtime-consistent experiment, even when a baseline
fails its retrieval gate. Inspect each strategy’s quality, safety, latency and paired regressions.
Exceptions preserve the failed request and partial report; never shrink denominators to pass.

2026-09-09 shared-corpus result at `.artifacts/m2/strategy-comparison-20260909T083207Z/report.json`:

| Strategy | Evidence cases | Required groups | Warm p95 seconds | Frozen retrieval gate |
| --- | --- | --- | --- | --- |
| Vector |22/26|22/27|0.219|Fail|
| BM25 |20/26|20/27|0.110|Fail|
| Hybrid |20/26|20/27|0.156|Fail|
| Vector + reranker |26/26|27/27|2.516|Pass|
| Hybrid + reranker |25/26|26/27|2.437|Pass|

All five have zero forbidden-source leaks and foreign-workspace404; overall/language targets
remain 90%/80%, with 3s warm p95. The default remains vector-rerank: hybrid newly fails Japanese
conflict case ja02 because fusion reduces two required groups in its23-candidate union to one
in the selected 20. Passing the aggregate gate does not excuse that paired regression.

Independent review tightened required/contiguous branch-rank validation after the measurement.
Twelve metric/freeze regressions pass; all 160 retained case/probe traces pass stricter validation
in the adjacent `strict-trace-validation.json`, bound to original report and validator hashes.
This is post-run structural revalidation, not a new latency/quality experiment. Original raw data,
corpus, scorer and thresholds remain unchanged. Candidate traces are API-filtered; separate real
PostgreSQL tests prove persisted candidate workspace isolation. These tuned development cases,
small latency samples and substring facts do not establish held-out or generation quality.

`generation_cli.py` now drives one persisted four-pipeline development comparison through the
authenticated API; see the [runbook](../docs/RUNBOOK.md#development-generation-comparison-cli).
It does not load the evaluator corpus, expected facts or scoring fixtures. Direct has no
retrieval; vector/hybrid baselines and the actual hybrid support graph retain distinct traces.
Manual contributions and reviewed system responses remain separate. The full frozen-case
generation responses/reviews and external-provider verification remain open.

`run_generation.py prepare --directory .artifacts/m5/NEW_BATCH` ingests the frozen corpus in
fresh development workspaces and admits all30 cases. `collect` with the same directory resumes
admission using stored keys and refreshes outcomes/individual request exports. Run from the
repository root with `uv run --project backend --frozen python evals/run_generation.py ...`.
Run one collector per directory. A failed ingestion is preserved and requires a new preparation;
admission or collection failures can be resumed. Reports reject changed frozen cases, runtime
or pipeline configuration. Each pipeline retains30 cases overall and10 per language, including
not-observed/failed/unfinished entries. Collection errors remain explicit beside last observations.
Exit0 means a validated collection snapshot, which can include unfinished/failed pipeline outcomes;
sequential API reads are not one database snapshot. It is not a passing generation-quality gate.
The 118 prepared requests in the September10 run await attributed contributions; two governed
cases exited for clarification. Submit through generation_cli.py, then recollect. Request files
contain one rendered request and its bindings; evaluator facts never enter application inputs.

`score_generation.py` validates the frozen [review rubric](generation-review-v1.json) against
its adjacent SHA256 lock and scores the original responses. Mechanical checks bind requests,
contributor/response hashes and exact active-version citation spans. Named reviewers judge
factual completeness, support, language, routing and safety with rationale; those assertions
are not authenticated proof of reviewer independence or automated semantic entailment.
The scorer requires a successfully validated collection report; invalid batch envelopes,
changed strategies and stale review bindings are rejected. Missing judgments stay in30/10
denominators. All cases need review before a pipeline can meet the frozen90%/80% development
target; invalid evidence or an unsafe judgment prevents a pass regardless of the aggregate.
See the [scoring command and review format](../docs/RUNBOOK.md#generation-review-scoring).


Local generation now has a separate execution/evidence path: `run_local_generation.py` prepares
and collects all30 frozen cases from an existing ingested corpus report; `score_local_generation.py`
uses `generation-review-local-v1.json` and its hash lock. See the
[local comparison commands](../docs/RUNBOOK.md#local-four-pipeline-comparison). Actual local
request/model/usage provenance has no fabricated human contributor. The prior manual reports,
runner and rubric remain unchanged. The local rubric retains90% overall/80% per language and
all five dimensions; it only reflects the approved automatic routine answer and set-aside
meaningless-input routing. Missing/failed cases remain in the denominators. The fixed local batch has120 reviewed observations: direct7/30, vector22/30, hybrid20/30,
system20/30. All frozen local targets failed; STATUS owns exact evidence. Attributed judgments
are not external-provider proof or automatic semantic truth.
