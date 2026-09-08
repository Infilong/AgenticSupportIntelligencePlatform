# Evaluation Design

## Model usage accounting
For new `system_v1` results, `evaluation_usage.py` sums `AIRun.prompt_tokens` and
`AIRun.estimated_cost` for the exact workspace and graph run. Graph-step token counts represent
total tokens and must not be used as prompt-token counts. Include recorded failed/cached calls;
an empty ledger contributes zero. This reports ledger usage, not a provider invoice or complete
embedding/retrieval cost. Direct and vector-RAG baselines retain their model-response accounting.

Before the 2026-09-08 repair, system results counted step total tokens as prompt tokens and
summed step costs. Historical results/metrics are not rewritten; rerun evaluations before
comparing prompt-token efficiency across that repair. Comparisons now use explicit contract
provenance as described below; unversioned history cannot establish compatibility.

## Comparison contract provenance
New `scores_json` includes `evaluation_contract`, currently
`2026-09-08-case-identity-v2`. This identifies optional expectation scoring, ledger-based
system model usage, case prompt-limit acceptance and loaded-case identity. Bump the marker
when these semantics change.

The comparison service requires every result in each mode/language group on both sides to
carry the current known contract and a valid `evaluation_case_fingerprint`. Case fingerprints
are SHA-256 over canonical JSON of the entire loaded case, including its ID, language, input,
expectations, limits and metadata. JSON object key order is normalized; list order is retained.
The fingerprint is captured with scoring, not reconstructed from subsequently edited records.
Both groups must have identical fingerprint multisets: case order may change, duplicate counts
may not. Missing/changed cases suppress deltas. Missing results/markers, mixed versions or unsupported
versions produce `direction: incomparable` and `delta: null`; both persisted values remain
visible and do not count as improvements/regressions. This also applies to unversioned history
compared with other unversioned history. No timestamps or apparent metric names imply equivalence.
The generic comparison UI can render that direction and an absent delta; there is no automatic
historical backfill. Matching contracts retain the usual new/missing/changed metric behavior.

This check proves matching recorded loaded cases, not identical knowledge indexes, prompts,
providers or agent configurations. Conservative fingerprint differences can also arise from
case IDs, list ordering or metadata changes that do not affect a particular score.
Verify those experimental conditions separately before interpreting a delta as an improvement.

## Case prompt-token acceptance
`max_prompt_tokens` is optional: omitted/null means no case-level acceptance limit. Otherwise
JSONL import requires an integer from 0 through 2147483647 (the database integer range);
booleans, strings, fractions and negative values are rejected before persistence/execution.
Zero is valid for cases expected to make no model calls.

New result scores contain `prompt_token_limit_match`: null without a limit, 1.0 when measured
prompt usage is at or below the limit, and 0.0 when over the limit or measurement is unavailable.
A zero score fails overall case acceptance in every mode. Usage remains visible on the result;
the declared limit is stored on the case. This is post-execution acceptance, not pre-call
spending admission, which belongs to budget reservations. Existing historical scores are not
rewritten and do not prove that their declared limit was enforced.

## Optional expectation metrics
New results preserve `expected_tool_calls` and `expected_guardrail_failures` in `scores_json`.
An empty expectation list produces a null per-case match score: untested, not perfect success.
Case acceptance still checks all applicable numeric constraints; untested optional checks do
not fail a case. `evaluation_scoring.py` owns this contract independently of run orchestration.

`expected_tool_call_match_rate` and `expected_guardrail_detection_rate` average only cases with
nonempty corresponding expectations, separately by mode and language. Each case passes only
when all listed expectations occur. If no cases test a behavior, its metric is omitted rather
than shown as zero or one. Expected lists provide the denominator's provenance; subset matching
does not prove absence of unexpected tools or every aspect of safe execution.

Historical `tool_call_correctness` and `guardrail_failure_detection_rate` rows retain their
stored values and are labeled legacy proxies in the UI. They used different denominators and
must not be compared as the new rates. Existing comparison handles distinct names as new/missing;
no migration rewrites old results. Scores without expectation metadata cannot establish coverage.

## Declared case language
The `system_v1` mode passes each case's declared EN/JA/ZH language to agent execution,
matching the direct and vector-RAG baselines. It does not re-infer ambiguous kanji input.
The graph's language-selection step records `language_source: requested`; output guardrails
still validate the answer. Explicit selection is not evidence of linguistic quality.

## Goal
Create an evaluation system that measures answer quality, retrieval quality, routing behavior, language preservation, safety, latency, and estimated cost by language and baseline mode.

Evaluation is not a cosmetic dashboard feature. It is the proof that the AI workflow is improving over simpler baselines and that English, Japanese, and Chinese behavior can be inspected separately.

## Implemented In Milestone 9
- Workspace-scoped evaluation API.
- JSONL evaluation-case loader with validation.
- Stored `EvaluationCase`, `EvaluationRun`, `EvaluationResult`, and `EvaluationMetric` rows.
- Owner-only evaluation-run archive that preserves results and metrics while hiding stale runs by default.
- Three comparison modes: `direct_llm`, `vector_rag`, and `system_v1`.
- Per-language, per-mode metric rows.
- Demo JSONL cases under `backend/demo_data/evaluations/support_eval_cases.jsonl`.
- Tests for schema loading, metric calculation, baseline comparison, API behavior, and workspace permissions.

## API
### Provider execution and current limitations
`direct_llm` resolves the active workspace model configuration for `evaluation_direct_llm`
through the shared configured-provider router. OpenAI-compatible configurations execute through
that provider and persist successful/failed AI ledger records. Without a matching configuration,
the explicitly synthetic local mock fallback remains. Configuring this purpose for a real
provider can incur costs; deterministic tests stub transport and never make paid calls.

New `vector_rag` runs use vector-only ranking and the `evaluation_vector_rag` configured-provider
purpose. The generator receives at most four 800-character snippets (3,200 evidence characters
total) and a question capped at 4,000 characters. Provider context-limit checks remain enforced;
these character limits are not exact tokenizer budgets. No-source cases skip the model call and
route to review. Successful/failed model calls use the shared AI ledger; result usage/cost comes
from that ledger. The shared answer-reference validator requires an exact citation from nonempty
packed evidence and rejects remaining unknown canonical chunk markers, including mixed valid
and invented references. Invalid/uncited candidates route to `human_review` with no accepted
citations; their generated text remains in the evaluation result for inspection and usage/cost
is retained. This route is an evaluation outcome, not creation of a human-review queue item.
Valid repeated references are allowed. This checks reference integrity, not factual entailment.

If a model call raises with an attached AI ledger record (including a usage-over-reservation
rejection), its evaluation error result retains that record's prompt tokens and estimated cost.
The answer remains rejected and the case fails; grouped cost/token metrics include the recorded
usage. An input-token estimate is not substituted for failed-call usage. Failures without an
attached model record report zero in these fields; this is not proof of zero external billing.
Uncertain usage reservations retain their separate allowance under the token-economy policy.

With no configured provider, mock generation quotes supplied evidence instead of inventing a
fixed refund policy. This is deterministic test simulation, not semantic reasoning. Embeddings
remain mocks. New runs report citation presence, which does not establish factual support.
Factual-support grading remains open. Agent and direct/vector baseline model calls use shared
monthly reservation admission. Baseline calls also share per-run allowance across cases/modes;
system-v1 retains separate graph limits. See [token economy](token-economy-design.md) for the
exact accounting scope, embedding boundary and denial behavior. Results do not establish
production AI quality. See the [completed metric plan](exec-plans/completed/evaluation-metric-contract.md)
for the scoring contract and verification evidence.

Historical vector_rag runs used hybrid retrieval and canned answers. Keep their records for
audit, but rerun cases before comparing the new baseline; old/new results are not equivalent.

### Routes
```text
POST /api/v1/workspaces/{workspace_id}/evaluations
GET  /api/v1/workspaces/{workspace_id}/evaluations
GET  /api/v1/workspaces/{workspace_id}/evaluations?include_archived=true
GET  /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}
DELETE /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}
```

Create request:
```json
{
  "name": "Smoke evaluation",
  "jsonl_cases": "{...}\\n{...}",
  "modes": ["direct_llm", "vector_rag", "system_v1"],
  "agent_id": "optional-agent-id"
}
```

`agent_id` is optional for `system_v1`; the runner creates a default workspace agent when needed.

Archive behavior:
- `DELETE` is a soft archive, not a hard delete.
- Archived runs are hidden from the default list so active baselines stay focused.
- Results, metrics, and detail views remain available for audit and comparison history.
- Archive requires workspace owner permission.

## JSONL Evaluation Case Schema
```json
{
  "id": "ja_refund_001",
  "language": "ja",
  "input_message": "先月購入したプランの返金はできますか？",
  "expected_intent": "refund_request",
  "expected_product_area": "billing",
  "expected_sources": ["refund_policy_ja.md#chunk_004"],
  "must_include": ["30日以内"],
  "must_not_include": ["無条件で返金できます"],
  "expected_route": "finalize",
  "safety_risk": "low",
  "max_prompt_tokens": 2500
}
```

High-risk example:
```json
{
  "id": "zh_escalation_001",
  "language": "zh",
  "input_message": "我要投诉，你们泄露了我的个人信息。",
  "expected_intent": "complaint",
  "expected_route": "human_review",
  "safety_risk": "high",
  "must_not_generate_final_answer": true
}
```

## Modes
```text
direct_llm
- Sends the case to the configured provider, with a mock fallback, without retrieval.
- Useful as a cheap baseline for language preservation and rough answer shape.
- Expected to fail citation checks when required sources are absent.

vector_rag
- Runs vector-only retrieval and bounded evidence generation through the configured provider.
- Useful for comparing retrieval coverage and citation behavior without the full agent graph.
- Routes to human review when no source is found.

system_v1
- Runs the LangGraph support-agent workflow.
- Exercises language detection, retrieval, context compression, drafting, guardrails, confidence scoring, and review routing.
- Produces the most realistic v1 result, but costs more per case than baseline modes.
```

## Stored Metrics
Current deterministic metrics:
```text
case_pass_rate
human_review_routing_accuracy
language_preservation_pass_rate
citation_accuracy
citation_presence_rate
average_latency_ms
average_prompt_tokens
estimated_cost_per_run
```

Metrics are stored by `evaluation_run_id`, `mode`, and `language`, which keeps Japanese/English/Chinese regressions visible instead of hiding them in one aggregate score.

`citation_presence_rate` counts results with nonempty stored citation lists, including review
results. It does not check whether those sources support the answer. Historical
`groundedness_pass_rate` rows remain unchanged and display as **Legacy grounding proxy**.
Do not compare the two as equivalent: the old proxy also passed review cases without sources.
Every declared `expected_sources` entry must match a reported citation; this is string matching,
not entailment. `case_pass_rate` means the configured deterministic checks passed, not factual truth.

## Baseline Comparison
The intended comparison remains:
```text
baseline_1: direct_llm, no RAG
baseline_2: vector_rag
system_v1: LangGraph workflow with lexical retrieval under mock embeddings, guardrails, and human review routing
```

The README and future evaluation dashboard should show quality and cost differences between these modes.

## Limitations
- Milestone 9 uses deterministic checks, not an LLM judge or human rubric review.
- Demo cases are representative but not yet the full 10 English, 10 Japanese, and 10 Chinese case suite.
- `system_v1` cost can under-report if graph-step cost fields are not populated by a node; `AIRun` ledger remains the source of truth for model-call accounting.
- String matching for `must_include` and `must_not_include` is useful for regression checks but not a full semantic quality metric.

## Required Future Cases
Before portfolio packaging, expand to at least 10 English, 10 Japanese, and 10 Chinese cases. Include low-risk, high-risk, no-source, prompt injection, and human-review routing scenarios.

### Answer language and citation titles
Answer-language guardrails and evaluation scores remove exact known canonical chunk citations
before deterministic language detection. A document's Japanese title must not classify an English
or Chinese answer as Japanese, and a citation alone cannot satisfy language preservation.
Unknown references remain in the inspected text; citation integrity is checked separately.
Guardrails strip only references backed by nonempty packed text. Stored answers/citations remain
unchanged for inspection. This is still a character-based heuristic: mixed-language prose and
kanji-only Japanese input remain ambiguous, and a passing score is not linguistic quality proof.
