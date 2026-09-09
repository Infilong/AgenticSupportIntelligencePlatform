# RAG design review and hardening

Checkpoint: audit and targeted repairs verified; full RAG hardening remains incomplete.
The design records outstanding M2 retrieval/context and M3/M5 generation/validation/evaluation
work. This checkpoint does not claim the attached brief's full stop conditions are satisfied.

## Execution brief

New direct user request on 2026-09-09: audit the current multilingual RAG implementation against
the supplied topology and failure taxonomy, polish material weaknesses, and write a durable RAG
design when useful. The attached RAG SYSTEM REVIEW AND HARDENING brief governs this task.
This is a deep, bounded RAG task; it does not resume unrelated imports or the entire M1–M6 goal.
Root owns implementation/docs; independent reviewers inspect ingestion/security and evaluation.
Start 04:48:37 UTC; stop this unattended task by 08:48:37 UTC or when the authorized audit/fix
scope is handled. No paid API, deployment, main/archive changes or large search infrastructure.

## Approach

1. Inspect ingestion, retrieval, context, generation, validation, traces and evaluation separately.
2. Record current/correct/weak/missing/complexity findings with code and dated evidence.
3. Reproduce suspected P0/P1 failures before selecting coherent repairs. Missing release capabilities
   are gaps, not proof of an exploit; passing provenance checks are not proof of semantic support.
4. Define the request→vector/BM25→ranking→context→model→answer→citations trace and failure contract.
5. Preserve EN/JA/ZH fixed evaluation criteria, expose missing baselines/metrics, independently
   review changes, verify affected boundaries, update freshness and commit/push small checkpoints.

## Initial findings to verify

- Current retrieval uses 20 exact cosine candidates and a local reranker; lexical terms are stored
  but neither independent BM25 nor hybrid fusion runs. Trace results retain only selected rows.
- Context packing limits UTF-8 payload bytes, not a complete model-token budget.
- Generation is an attributed development handoff, with no external LLM dispatch or billing proof.
- Citations validate supplied source identity and exact quotations, not claim entailment.
- Current frozen retrieval evidence is a tuned 26-case/27-group result; inspect evaluator coverage
  before treating it as accuracy/trustworthiness evidence for the full RAG pipeline.

The dedicated design must distinguish detected runtime faults, expected safe abstention and
evaluation-only quality failures; successful ACL exclusion must never be reported as a leak.

## Audit triage before repairs

Confirmed P1: ingestion's artificial 8,000-character safety blocks reset chunk overlap and can
split an exact identifier/fact into pieces absent from every chunk. Independent actual-function
reproduction: `"x " * 3999 + "ERROR-8421 means contact support immediately."`; the identifier
is split as ER / ROR-8421. EN/JA/ZH offset-only tests do not catch this. Repair continuity at
safety-block boundaries while preserving heading boundaries, tokenizer limits and cancellation.

P2 with demonstrated benefit: evaluation can combine a required heading from one passage with
an unrelated factual substring elsewhere and falsely pass; non-evidence cases' excessive result
counts are not part of the global gate. Add adversarial scorer regressions before repairs.
Other missing BM25/fusion/token-budget/generation/validation capabilities remain design gaps;
do not label them implemented or call the full RAG stop conditions satisfied.

## Repair evidence and review

- Original boundary regressions reproduced three failures. Carrying the final chunk fixed them.
- Expanded multi-boundary coverage exposed ordinary recursive splitting of an unseparated
  EN/CJK span, reproduced independently without safety blocks. The fixture now uses a paragraph
  boundary to isolate the intended defect without weakening fact assertions.
- Sentence punctuation could also become a separate passage. Explicit end separators fix this;
  23 backend unit tests pass in 15.67s at
  `.artifacts/m0/backend-20260909T050956951297Z`. The preceding failed wrapper is retained at
  `.artifacts/m0/backend-20260909T050835843553Z`. Upstream AnyIO deprecation remains visible.
- Two scorer regressions failed before the fix; all seven scorer checks pass afterward.
  Corpus v1 hashes remain unchanged. New reports identify the stricter scorer.
- Independent ingestion/security review found no remaining blocking source defect; it requires
  freshly indexed runtime evidence because stored chunks do not change automatically.
- Independent evaluation/design review approved the bounded scorer repair and design, retaining
  source-bound qrels, measured BM25 choice, and staged trace implementation as explicit gaps.

- 113 PostgreSQL integration tests pass in 191.96s with unchanged source during the run:
  `.artifacts/m0/integration-20260909T051214666582Z`.
- The four-service isolated runtime rebuilt successfully. Fresh actual EN/JA/ZH ingestion and
  vector/reranker probes preserve all three boundary facts:
  `.artifacts/rag-hardening/boundary-20260909T051641Z/report.json`.
- Frozen long-corpus evaluation: 26/26 cases, 27/27 groups, warm p95 2.406s, zero leaks,
  foreign access 404; source/runtime unchanged:
  `.artifacts/m2/retrieval-eval-20260909T051734Z/report.json`. Four generation/routing
  outcomes remain unverified. No fixture/threshold was weakened; this is not held-out quality.
- Both knowledge browser journeys pass in 10.3s at `.artifacts/rag-hardening/knowledge-ui/`;
  desktop/mobile screenshots inspected. Actual Chrome verifies Japanese search and exact-source
  navigation at offset 7956. Initial source opening displayed only the first 4,000 characters
  as designed; following the retrieval link opens the fact, not the beginning of the document.
- Backend Ruff lint/format pass. Baseline commit 83f4f8d CI run 34312120990 passed.
- Review attribution corrected: the earlier user topology names BM25 candidates; the attached
  audit brief calls for measured lexical/hybrid comparison. Parameters remain an evaluation choice.
