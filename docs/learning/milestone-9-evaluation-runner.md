# Milestone 9: Evaluation Runner

## What Was Built
Milestone 9 added a workspace-scoped evaluation runner. It loads JSONL evaluation cases, runs selected modes, stores per-case results, and computes per-language metrics.

The implemented modes are:
- `direct_llm`: a no-retrieval baseline through the mock model provider.
- `vector_rag`: retrieval plus cited answer assembly.
- `system_v1`: the full LangGraph support-agent workflow.

## Why Companies Care
AI teams need evidence that a system is improving, not just demos that look good. Evaluation lets teams compare baselines, catch regressions, measure multilingual behavior, estimate cost, and defend whether an LLM workflow is production-ready.

For Japan-facing AI companies, per-language evaluation matters because Japanese, English, and Chinese failures often have different causes: tokenization, retrieval coverage, tone, policy phrasing, or language preservation.

## How This Project Uses It
The project stores `EvaluationCase`, `EvaluationRun`, `EvaluationResult`, and `EvaluationMetric` rows under workspace boundaries. Each run can compare `direct_llm`, `vector_rag`, and `system_v1`, then report metrics by language and mode.

This creates an interview-ready story: the platform does not only run an agent; it measures routing accuracy, citation behavior, groundedness, language preservation, latency, prompt tokens, and estimated cost.

## Design Tradeoffs
- Deterministic checks are simple, fast, and testable, but they miss semantic nuance.
- Synchronous local execution is easier for v1, but async queue execution will be better for large evaluation suites.
- JSONL input keeps eval cases portable and reviewable, but future admin UI will need case management.
- Baseline modes are intentionally simpler than `system_v1`; their value is comparison, not feature parity.

## Failure Modes
- Aggregating all languages together can hide Japanese or Chinese regressions.
- Weak `must_include` strings can make tests too easy or too brittle.
- Evaluation routes can leak data if workspace filters are missed.
- Baseline results can look worse by design; docs must explain what each mode is proving.
- Cost numbers can be misleading unless the AI run ledger and graph-step cost rollups stay aligned.

## Interview Explanation
A strong explanation is:

"I added a deterministic evaluation runner so the AI platform can compare a direct LLM baseline, a retrieval baseline, and the full LangGraph workflow. Results are stored by workspace, mode, and language. The system measures routing accuracy, citation accuracy, groundedness, language preservation, latency, prompt tokens, and estimated cost. I used deterministic checks for fast regression testing and documented that they complement, not replace, human review or LLM-as-judge evaluation."
