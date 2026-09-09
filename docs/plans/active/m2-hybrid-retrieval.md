# Measured multilingual BM25 and hybrid retrieval

## Execution brief

User outcome: actual independent lexical/vector retrieval with inspectable ranking stages,
within the small local stack (RAG, TRACE, TENANT, UX). Continue the full M1–M6 goal and existing
September 9 06:04:24–10:04:24 UTC window. Base `ffc730a`; no paid API, merge, deployment or
archived-data changes. Root owns implementation; independent agents review bounded source,
security/query behavior and evidence. Deep work: additive schema, permissions and API contracts.

Current vector20→local reranker is verified but is not BM25/hybrid retrieval. Existing unique
lexical terms cannot supply term-frequency saturation or length normalization. Reviewer confirmed
the need for complete active-population metadata, nullable absent scores and bounded query terms.

## Frozen initial design (before measurement)

- Add per-chunk term frequencies, lexical length and versioned recipe. Preserve source text,
  offsets, vectors, versions and legacy unique terms. Backfill immutable text in bounded batches;
  missing metadata must never masquerade as a valid empty-token document. Reject lexical/hybrid
  queries if the authorized active population is incompletely indexed.
- Recipe: NFKC then casefold on derived keys only; ASCII alphanumeric words/whole hyphen or
  underscore identifiers plus their components; overlapping CJK bigrams, single-character runs
  retained. No stopword list/stemming. Length counts all emitted occurrences, including components.
  Query terms are unique; at most 128 distinct terms, otherwise explicit bounded-input rejection.
- Same workspace/current-version/not-withdrawn/embedding-space population for vector, BM25 and
  collection statistics. BM25 positive IDF `ln(1+(N-df+0.5)/(df+0.5))`, k1=1.2, b=0.75;
  zero-token chunks remain in population statistics and never match. Empty population returns none.
- Candidate funnel: vector20 + BM2520 → identity union<=40 → equal-weight RRF, one-based ranks,
  k=60 → top20 → existing reranker → final K. Absent branch rank contributes zero; deterministic
  chunk-ID tie breaks. Do not collapse different sources with equal text or suppress conflicts.
- Record recipe, raw scores/ranks, fusion/pre-rerank/final selection and exclusions without
  duplicating passage bodies in traces. BM25-only must not call embedding/reranking providers;
  absent cosine stays null. Expose progressive trace detail in knowledge/workflow inspection.
- Retain current default until unchanged frozen-corpus comparison and isolation/latency gates pass.
  Compare vector-only, BM25-only, hybrid-only, current vector+reranker and hybrid+reranker on the
  same newly ingested corpus. This is retrieval comparison, not four answer-generation baselines.

Design references: [Stanford BM25](https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html),
[Lucene positive IDF](https://lucene.apache.org/core/9_12_1/core/org/apache/lucene/search/similarities/BM25Similarity.html),
[RRF paper](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf). These motivate initial parameters;
they are not evidence of this application's performance or optimal tuning.

## Ordered slices and verification

1. Lexical metadata/migration, shared source population, SQL BM25 and pure RRF. Verify exact
   formula, saturation/length, scoped DF/statistics, Unicode/repeated query/empty/ties, populated
   migration rollback/retry and unchanged citations/vectors. Inspect SQL plans on real PostgreSQL.
2. Strategy integration and bounded trace contract/UI. Verify provider call selection, errors,
   concurrent withdrawal/revocation, source permissions, generated API types and actual browser.
3. Identical frozen-corpus comparison plus separate source-bound identifier/cross-language cases;
   measure 50k chunks/common-term/CJK queries separately from the completed message benchmark.
   Preserve failed runs and thresholds; no default switch based on a flattering aggregate alone.
4. Independent review, owning docs/receipts, relevant regression/prep, commit/push coherent steps.
   Keep semantic validation, complete token budget and remaining release gates explicit.

Stop at the existing unattended boundary or real blocker; checkpoint unfinished work clearly.

## Foundation results and repairs

Implemented additive metadata/migration, one active source population, internal SQL BM25 and
pure RRF. No HTTP strategy or default switch yet. Initial migration used an incomplete predecessor
ID; isolated setup failed at `.artifacts/m0/hybrid-foundation-20260909T073540376065Z` before any
runtime migration. Corrected to actual `0009_attempts`; seven focused cases passed at
`.artifacts/m0/hybrid-foundation-20260909T073754137539Z`.

Independent review found JSON null differed from SQL NULL. Guard now rejects non-object JSON;
fullPG120 passed at `.artifacts/m0/integration-20260909T073947426228Z`,42 units at
`.artifacts/m0/backend-20260909T074003564706Z`. Expanded SQLNULL→JSONnull fixture initially assigned
None to an already-None value and emitted no update (failure saved at
`.artifacts/m0/hybrid-foundation-20260909T074758192605Z`); restore a valid object between the two
distinct representations. Populated504-row migration test preserves exact evidence, injects
interruption after500 writes, proves rollback, then successfully retries.

Live backfill:1284 retained chunks,0 incomplete; pre-migration dump retained under
`.artifacts/rag-hardening/before-lexical-20260909.dump` (not restoration proof). Review identified
old writers could insert between backfill and service recreation. Both up/migrate now build then
finish bounded API/worker stop before migration; failures do not restart old writers. Three
command-order/failure tests pass. Real guarded startup follows; no real concurrent legacy-writer
shutdown injection is claimed. Foundation does not complete trace integration or50k-chunk proof.

Final focused seven checks pass at `.artifacts/m0/hybrid-foundation-20260909T075059400220Z`.
Real guarded `up` completed after observed build → API/worker stopped → migrations/checkpoints →
healthy API/frontend/worker/PostgreSQL. Final output tail (excluding build/stop prefix) is retained
at `.artifacts/rag-hardening/guarded-up-tail-20260909T0752.log`. Code review supports the ordering;
no simultaneous legacy writer was injected during real Docker shutdown.
