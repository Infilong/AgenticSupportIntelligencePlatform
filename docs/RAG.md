# RAG system: design, audit and hardening contract

Owner: backend retrieval/ingestion/workflow plus evaluation. Reviewed against checkpoint `83f4f8d`
on 2026-09-09. [The execution record](plans/completed/rag-design-hardening.md) owns subsequent fixes
and verification. This document separates current code from the required target; it does not
claim that hybrid superiority, automated grounding validation or external generation already work.

## RAG AUDIT

**Historical audit pipeline (2026-09-09):** permission-gated knowledge → versioned chunks/vectors → authorized exact vector
search → local reranker → bounded evidence snapshot → durable development handoff → cited draft
→ human review. That checkpoint used real retrieval/workflow with simulated generation.

Current ordinary local mode uses real LangChain/Ollama inference and versioned routing: supported
automatic answer, exception review, missing-support intervention or retained set-aside outcome.
Source IDs and publication authority are checked independently of the model; classification
and claim support still require evaluation. Manual/frozen comparisons preserve their older mode.
This update does not change frozen retrieval targets or establish full semantic-quality gates.

**Correct boundaries inspected:** immutable original bytes/checksums; normalized-text offsets;
workspace and active-version restrictions before candidate materialization; revalidation after
inference and before publication; pinned local models; fenced jobs; retained uncertain executions;
exact-quote provenance; separate original/draft/approved result and human decision.

**Weak at audit baseline:** safety-block chunk continuity, evidence-quality scoring, token budgeting, duplicate
evidence handling and trace completeness. **Missing:** measured hybrid default selection, full model-call
correlation/accounting, source-bound semantic validation and four comparable answer pipelines.
**Unnecessary complexity:** no additional search service, Redis, ANN index, graph database or
agent framework is justified. Keep PostgreSQL exact search until measurements justify a change.

## Required topology

```text
HTTP request_id → authorized workspace + actor → message_id / run_id / attempt
                                                   ↓
                                      original + processed query
                                                   ↓
                                            retrieval_trace_id
                                      ┌────────────┴────────────┐
                                      │                         │
                           vector candidates              BM25 candidates
                           cosine score + rank            BM25 score + rank
                                      └────────────┬────────────┘
                                           rank fusion
                                         optional reranking
                                                   ↓
                                  final ranking → selected evidence
                                                   ↓
                           context manifest + exact payload hash + token budget
                                                   ↓
                                model_call_id (or explicit development handoff)
                              provider/model/revision, tokens, latency, cost
                                                   ↓
                                              draft answer
                                                   ↓
                                  citations → claim-support validation
                                                   ↓
                           answer / clarification / insufficient evidence / review
```

Vector and BM25 search run independently over the **same authorized active source population**.
ACL restriction precedes scoring in both branches; later revalidation handles permission/source
changes during processing. Filtering global results after retrieval is not an acceptable substitute.

Use distinct identities: each HTTP request, business attempt, retrieval and provider retry has
its own ID. Persist their relationship; polling requests must not overwrite originating request
identity. A linked customer reply creates a new attempt/context, never a reused approval.
The current middleware creates HTTP IDs, but does not persist this entire correlation chain.

## RAG REVIEW REPORT

| Stage | Current implementation and evidence | Gap / required change |
| --- | --- | --- |
| 1. Architecture | Real PostgreSQL/local-model retrieval and durable LangGraph; [current topology](ARCHITECTURE.md), [workflow tests](../backend/tests/integration/test_support.py) | Keep the small local stack; generation remains a development handoff. |
| 2. Ingestion | Admin-only UTF-8 TXT/Markdown, 5 MiB; original bytes retained. [service](../backend/app/modules/knowledge/service.py) | PDF/DOC/OCR are deferred beyond V1. Markdown ATX headings are recognized; tables/code fences/hierarchy need explicit supported semantics before expansion. |
| 2. Ingestion: normalization | BOM/newline handling, exact normalized-text spans | Apply NFKC/case normalization to **derived search keys**, preserving original text and citation offsets. Do not silently rewrite quoted policy. |
| 3. Chunking | Position-carrying [adapter](../backend/app/modules/knowledge/span_splitter.py) with LangChain merge/join hooks; 350 tokenizer units, 45 overlap, punctuation/paragraph/CJK separators, 1,000-chunk limit. [splitting](../backend/app/modules/knowledge/splitting.py) | Boundary identifier loss and repetitive-occurrence offsets repaired; compatibility tests guard private hooks on dependency upgrades. Do not tune chunk sizes without comparison. |
| 4. Metadata/versioning | Workspace/version/chunk IDs, section, offsets, checksum, token count, embedding space; atomic active-version switch. [models](../backend/app/modules/knowledge/models.py), [ingestion](../backend/app/modules/knowledge/ingestion.py) | Persist source language and chunker/index recipe; page only for a supported parser, never invented for TXT. Document model-change/reindex lifecycle. |
| 5. Embeddings | Real pinned multilingual E5-small, 384 dimensions, normalized query/passage vectors, 512-token rejection; no runtime fallback. [provider](../backend/app/providers/local_embeddings.py) | Validate returned batch identity/dimension against the configured space; test incompatible same-dimension models. Current production provider is fixed, so live mixing was not demonstrated. |
| 6. Vector retrieval | Exact cosine SQL top 20; default final 5, API maximum 10. Workspace/current-version/model-space filters precede materialization. [retrieval](../backend/app/modules/knowledge/retrieval.py) | Compare candidate/final K explicitly; similarity is not calibrated relevance probability. |
| 7. Lexical retrieval | HTTP-selectable SQL BM25 uses persisted term frequencies, length and active scoped collection statistics; Unicode recipe and populated backfill tested. [BM25](../backend/app/modules/knowledge/bm25.py) | One shared frozen-corpus comparison is complete; held-out evidence and50k-chunk performance remain pending. Unique-term overlap is not BM25. |
| 8. Hybrid retrieval | Pure equal-weight RRF preserves branch scores and identity ranks. [fusion](../backend/app/modules/knowledge/fusion.py) | Explicit hybrid strategies connect a union <=40 to top20 before optional reranking. Default stays vector-rerank after a measured hybrid conflict-case regression. |
| 9. ACL/security | Workspace membership before embedding/search; source/actor rechecks; foreign IDs denied. [retrieval tests](../backend/tests/integration/test_retrieval.py) | Retain the same restrictions in BM25, fusion, trace lookup and citation inspection. No leak was found in this bounded audit; this is not a completed security certification. |
| 10. Reranking/dedup/context | Pinned multilingual cross-encoder scores up to 20 pairs, truncated to 512 pair tokens. No explicit overlap/diversity suppression. [reranker](../backend/app/providers/local_reranker.py) | Trace truncation and evidence lost from model input. Measure vector vs reranked quality/cost. Deduplicate by provenance/overlap; do not collapse genuine policy conflicts. |
| 10. Context budget | Consider the existing top five in rank order; omit oversized complete snapshots and try later candidates within 24,000 UTF-8 JSON bytes. Context hash, no source-string truncation. [context](../backend/app/modules/support/context.py) | Full tokenizer-aware prompt+query+conversation+evidence+reserved-output budget; record excluded sources/reasons and token counts. Bytes are a transport bound, not a model budget or deduplication. |
| 11. Generation | Manual graphs pause for attributed contributions; configured ordinary local graphs now call LangChain/Ollama and record usage and routing. [Current topology](ARCHITECTURE.md) | No paid/cloud connectivity or full semantic-quality proof. Local input usage is in the ledger, returned output usage in the stored response; development wait is not inference latency. |
| 12. Citations | Supplied chunk ID, exact quote, current source/version, offset and checksum checks | Claim entailment/completeness is separate. Valid ID + plausible quote cannot establish that the answer is supported. |
| 13. No-source/review | New local routing separates automatic answers, exception review, missing-support intervention and set-aside input; historical manual behavior remains | Nonempty nearest neighbours can still be irrelevant. Model classification and conservative server backstops are not calibrated relevance, grounding or policy correctness proof. |
| 14. Multilingual behavior | EN/JA/ZH queries, same-language instruction, multilingual embedding/reranker | Test output language and forced cross-language source directions independently; UI language acceptance is not multilingual RAG proof. |
| 15. Evaluation | Frozen real API retrieval runner, per-language success@5/section recall@5, leakage and latency. [runner](../evals/run_retrieval.py) | No full Precision/Recall@K sweep, held-out generalization, answer/citation support or direct/vector/hybrid/system comparison. |
| 16. Observability | Retrieval final IDs/scores, graph steps, embedding/rerank input tokens/duration/charge, uncertainty and human decisions | Bounded vector/BM25/fusion/reranker/final candidate stages and exclusions are now saved and visible. Context selection and full origin correlation remain pending. Output tokens, generation pricing/version and complete failure taxonomy remain missing. |

## Retrieval and context decisions

Keep exact pgvector retrieval for the current small workload. Its exactness describes nearest
neighbour calculation, **not perfect semantic evidence recall**. See the
[pgvector documentation](https://github.com/pgvector/pgvector).

BM25 must preserve term frequency, document length and document frequency for the authorized active
index generation. Normalize query/index keys consistently: Unicode NFKC/case folding, whole exact
identifiers plus useful components, EN terms and a documented CJK n-gram baseline. Halfwidth kana,
fullwidth digits/hyphens and mixed-script identifiers need regressions. Keep punctuation handling
versioned. Lexical search need not translate; vector retrieval supplies cross-language recall.

The current recipe is `nfkc-identifiers-cjk-bigrams-v1`: NFKC/casefold derived keys,
ASCII words/whole hyphen-or-underscore identifiers plus components, CJK overlapping bigrams
and single-character runs. Length counts all emitted occurrences, not unique keys or model
tokens. Query terms are unique and limited to 128; excess is rejected without truncation.
Initial BM25 uses positive IDF `ln(1+(N-df+0.5)/(df+0.5))`, k1=1.2, b=0.75; zero-length chunks
remain in scoped population statistics but never match. Each branch returns at most 20;
RRF uses one-based ranks, k=60, equal weights and chunk-ID ties. Missing ranks contribute nothing.
These are frozen starting parameters, not tuned superiority. Migration 0010 preserves historical
evidence while backfilling frequencies/length/recipe in bounded reads. Missing SQL/JSON metadata
fails closed. Five explicit strategies are implemented: vector, BM25, hybrid, vector-rerank and
hybrid-rerank. BM25-only invokes no model; hybrid query bounds are checked before embedding.
Candidate stages commit before reranking so failures retain discovery evidence without invented
final ranks. Post-inference revalidation covers every candidate. Migration0011 leaves old stage
history unavailable. A workspace-authorized trace API powers progressive inspection and exact
source links. The [shared-corpus comparison](../evals/README.md#five-strategy-retrieval-comparison) keeps the
default vector-rerank:26/26 evidence cases versus25/26 hybrid-rerank, with a lost conflict source.
Both pass aggregate gates, but a tie or regression does not justify default replacement.
Held-out/50k-chunk proof remains in the [hybrid plan](plans/active/m2-hybrid-retrieval.md).

Use rank fusion because BM25 scores and cosine similarities have incompatible scales. Version
the reciprocal-rank constant/weights and tie-breaking rule; record each branch's contribution.
Missing candidates contribute nothing. Select parameters using the same frozen development cases,
then evaluate held-out cases. [Original RRF paper](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf).

Context packing selects complete evidence under the target model's tokenizer and remaining input
budget, with an explicit output reservation and overhead allowance. Keep instruction, customer
content and evidence distinct. Try another fitting candidate rather than abandoning selection
because one is too large. Any excerpt/compression retains original offsets and claim provenance.
Deduplication must retain required facts and conflicting authoritative passages. Do not use raw
long documents as context or claim a compression benefit without measuring it.

## Trace and accounting contract

Each stage records status, attempt, parent IDs, algorithm/configuration version, monotonic duration
and safe error code. Persist bounded candidate IDs, document versions, original ranks/scores,
fusion/rerank ranks, exclusion reasons and final selection. Resolve passage text only through a
permission-gated source view; do not duplicate customer text in ordinary logs.

The context manifest records selected source IDs/offsets, input components' token counts, tokenizer,
prompt version, exact serialized-payload hash, input limit and output reservation. Store payloads
only in authorized persistence with an explicit retention policy; hashes alone cannot reconstruct
lost evidence. An admin sees progressive detail, not every internal field on the inbox.

Model attempts record provider/model/revision, input/output/cached tokens where supported, wall and
provider latency separately, pricing version/currency, estimated vs billed cost, and uncertainty.
Local external charge zero is not zero compute cost. Missing usage remains null/unknown, never
invented zero. A development contribution is a handoff, not a fabricated OpenAI API call.

## Failure system

Use a stable `category`, `code`, `stage`, severity, retryability, detection method, evidence IDs,
attempt and chosen outcome. Diagnostic details are permission-gated and redact secrets/customer
bodies. Failures and expected safe outcomes are different: ACL exclusion and justified abstention
are normally successes. Aggregate by cause; do not label every bad answer a retrieval failure.

| Category/code | Detection and proof | Recovery / safe outcome |
| --- | --- | --- |
| ingestion/parsing_failed | Decoder/parser exception; malformed fixtures | Reject new version; preserve previous active version; explain supported format. |
| ingestion/chunk_evidence_lost | Boundary/coverage/identifier fixtures and source offsets | Fail indexing if integrity is broken; repair splitter and reindex a new version. |
| ingestion/stale_version | Compare active version at selection and publication | Discard/retrieve fresh evidence; never silently use superseded policy. |
| retrieval/recall_miss | Relevant gold evidence absent from candidates; runtime can only report observed zero/weak evidence | Diagnose indexing/tokenization/K/filters; avoid unsupported answer. |
| retrieval/ranking_miss | Gold evidence in candidates but removed by ranking | Inspect branch/fusion/reranker stages; compare unchanged cases. |
| retrieval/acl_leak | Any unauthorized candidate/context/citation observed | P0, fail closed and stop publication; retain security evidence. Successful exclusion is not this failure. |
| retrieval/acl_overfilter | Authorized gold source incorrectly excluded | Correct scope/index filtering; do not broaden access to hide a recall problem. |
| context/excess_noise | Labelled relevance and redundant-token measurements | Remove irrelevant/duplicate evidence with coverage checks. |
| context/evidence_lost | Selected required source omitted or truncated from packed context | Repack or review; preserve conflict/exception facts. |
| context/token_overflow | Full model-token accounting before dispatch | Repack or return a clear bounded-input error; never rely on silent provider truncation. |
| generation/unsupported_claim | Claim-level source review/evaluation; detector uncertainty explicit | Withhold approval, regenerate within a bound or request human review. |
| generation/ignored_evidence | Answer contradicts/omits required source facts | Review/regenerate; retain draft, context and validation result. |
| generation/wrong_language | Language checks plus EN/JA/ZH/mixed-script human cases | Correct or review; do not misclassify quoted identifiers as wrong-language output. |
| validation/invalid_citation | Foreign/missing/not-retrieved IDs, wrong offsets or false quotes | Reject contribution/publication; no ungrounded fallback. |
| validation/unsupported_citation | Valid citation fails claim support or contradicts the claim | Reject approval/review; distinguish from ID validation. |
| validation/false_confidence | Unsupported probability claim, failed calibration or contradictory signals | Remove probability claim; show specific uncertainty/review reasons. |
| infrastructure/provider_or_worker_failed | Timeout, unavailable model, lost lease/session, malformed result | Bounded safe retry; a crashed dispatched call remains uncertain until reconciled. |

Hallucination, bad ranking and confidence errors are not perfectly observable at runtime. Tests
and human annotations must distinguish measured failures from heuristic suspicion. Do not invent
an automatic detector or a trust score to fill the taxonomy.

## Accuracy, efficiency and trustworthiness tests

Keep the original frozen v1 corpus and dated results. Create a separately versioned corpus/scoring
contract for expanded judgments; freeze thresholds **before** tuning. Include long company policies,
version replacements, conflicting policy sections and exact identifier facts at chunk boundaries.
Relevance judgments bind workspace/source/version/section/fact, not headings and words independently.

| Layer | Measurements and required cases |
| --- | --- |
| Ingestion | Parse/version/withdrawal/rollback, boundary fact coverage, offsets, model-space compatibility, indexing duration and chunk counts. |
| Retrieval | Vector-only, BM25-only, hybrid, hybrid+reranker on identical cases; K=3/5/10/20 candidate/final cutoffs identified separately. Precision@K, evidence recall@K, MRR where useful, group/fact coverage, per-language denominators and forbidden-source count. |
| Context | Gold evidence retained, irrelevant/duplicate token fraction, packed input size, truncation/overflow and cost of packing. |
| 11. Generation | Factual correctness, grounded claim fraction, important-claim coverage, citation support, answer-language correctness and appropriate clarification/refusal/review. |
| End-to-end | `direct_llm`, `vector_rag`, `hybrid_rag`, `system_v1` with the same question/generation settings and budget. Each pipeline must actually differ as declared; unsupported pipelines are unavailable, not fake green baselines. |
| Efficiency | Stage and end-to-end p50/p95, cold vs warm, queue/human-wait separately, tokens, external cost and recorded local hardware/corpus size. |
| Trustworthiness | Valid-but-irrelevant citation, contradictory citation, one supported plus one invented claim, stale/foreign/injected evidence, meaningful abstention, uncertainty and failure recovery. |

For each language include answerable, paraphrased, exact identifier, no evidence, conflict,
injected document and review-required cases. Explicitly require EN→JA, JA→EN, ZH→EN and EN→ZH
source directions in their own cases; translation alternatives must not accidentally bypass them.
Define Precision@K's denominator when fewer than K results exist, and distinguish recall of
annotated relevant chunks from recall of required fact groups. Report unsupported/empty denominators
as unavailable, not 100%. Model judges supplement deterministic checks and human annotations.

Do not show LLM self-confidence as a probability. Prefer inspectable evidence/validation/risk
signals. If probabilities are ever exposed, require held-out labelled calibration (e.g. Brier/ECE),
coverage and error analysis before routing depends on them.

Historical v1 evidence: 26/26 evidence cases, 27/27 groups, 2.5s warm p95 in
`.artifacts/m2/retrieval-eval-20260908T170142Z/report.json`. It is a tuning-corpus result under the
older scorer, not held-out semantic proof. Four outcome cases were not generation-verified.
The 113-case PostgreSQL and ten browser checkpoints in STATUS prove software flows, not all metrics
above. Fresh hardening evidence and any score changes must be reported without overwriting history.

## 18. Remaining limitations and 19. Recommended next improvements

- **P0:** no confirmed cross-workspace leak in this audit; zero leakage remains mandatory.
- **P1 resolved here:** demonstrated chunk-boundary evidence loss. Missing semantic validation/
  abstention and provider-generation gates still block a full production RAG claim.
- **P2 resolved here:** demonstrated scorer false positives/result bounds. Remaining: measured hybrid selection,
  complete traces/token accounting, source-aware evaluation and runtime failure categories in coherent slices.
- **P3:** remove avoidable candidate metadata round trips or add caches only after profiling.

An audit/documentation checkpoint is not completion of RAG hardening. Full completion requires
critical EN/JA/ZH, isolation/version, measured citation-support/no-source, browser/runtime and
diagnosable trace gates. No paid API is authorized. Unavailable live generation evidence stays
explicit; code presence, manual development responses and valid citation IDs cannot replace it.

## 17. Fixed issues and operational limits

The September 9 repair carries the final chunk across artificial work boundaries and retains
sentence separators at the end of passages. Real headings reset continuity, including repeated
heading titles. This does not guarantee that every arbitrary multi-sentence fact fits a chunk:
long unseparated mixed-script spans can still split structurally. Measure evidence coverage.
Existing stored chunks do not change automatically; replace/re-index affected documents through
normal versioned ingestion. Preserve prior active versions until replacement indexing succeeds.

The subsequent [span/context repair](plans/completed/rag-span-context.md) resolves two reproduced
P2 defects: repetitive text mapped to an earlier matching occurrence, and a large candidate
preventing later fitting evidence from being packed. Positions now travel through partitions
and LangChain merge/join hooks, including whitespace trimming; carry uses the same actual span.
This does not rewrite existing chunks or establish semantic citation support.

Scorer `active-required-sections-v2` counts facts only from active returned top-five passages in
required sections and enforces negative-probe result limits. It still cannot bind each fact to
its particular document/version or individual evidence group when headings repeat. Source-bound
judgments need a new frozen evaluation version. Historical scores retain their original meaning.

## 15. Evaluation results at the repair checkpoint

- 23 backend unit tests and 113 PostgreSQL integration tests pass; exact commands/artifacts are
  in the execution record. [Boundary regressions](../backend/tests/unit/test_chunk_boundaries.py)
  and [scorer regressions](../scripts/tests/test_retrieval_scoring.py) preserve the reproduced failures.
- Freshly ingested EN/JA/ZH boundary facts all return intact through actual local models and
  PostgreSQL: `.artifacts/rag-hardening/boundary-20260909T051641Z/report.json`.
- The unchanged long-policy corpus passes 26/26 evidence cases and 27/27 groups under the
  stricter scorer: EN 8/8, JA 9/9, ZH 9/9; warm p95 2.406s, zero forbidden leaks, foreign request
  denied with 404. Evidence: `.artifacts/m2/retrieval-eval-20260909T051734Z/report.json`.
  All 30 queries ran; four routing/generation outcomes remain unverified. Runtime and source
  hashes were unchanged during measurement. This remains a tuned corpus, not a held-out test.
- Two existing knowledge browser journeys pass: upload/search, failed replacement, withdrawal/
  restoration, source inspection and mobile viewer controls. Report/screenshots/traces:
  `.artifacts/rag-hardening/knowledge-ui/`. Actual Chrome also retrieved the Japanese boundary
  fact first and opened its exact version at offset 7956 without horizontal overflow.
- Browser inspection also showed repeated policy uploads filling several results and unrelated
  filler below the correct boundary fact. This supports the documented dedup/noise evaluation
  priority; do not report top-five passage precision as 100% from case success.
- Full answer/citation support, live generation, four end-to-end baselines and complete failure
  taxonomy are **not verified**. No new frontend behavior, API contract or database migration was
  introduced by this repair. Existing browser evidence is scoped to knowledge workflows.

Subsequent span/context evidence (September 9): 39 units and 116 PostgreSQL tests pass; three
newly ingested real EN/JA/ZH boundary facts remain intact. The unchanged frozen corpus passes
26/26 cases and 27/27 groups, warm p95 2.672s, with zero forbidden leakage. See
`.artifacts/m2/retrieval-eval-20260909T072217Z/report.json` and the linked repair record.
Generation remains unverified; these results do not add held-out semantic proof.
