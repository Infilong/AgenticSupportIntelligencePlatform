# Honor configured evaluation providers

## Goal
Stop direct-LLM evaluations from bypassing configured providers with unconditional mock execution.
## Context
The runner calls MockModelProvider directly even for an active OpenAI-compatible purpose config.
New transport-spy regressions fail because no configured provider call occurs.
## Requirements
Use the shared provider router for evaluation_direct_llm; preserve the explicit local mock fallback,
workspace config resolution, recorded usage/cost and explicit failed-case behavior.
## Non-goals
RAG baseline repair, groundedness judging, spend admission or actual paid verification.
## Acceptance Criteria
Stubbed configured transport is invoked; its answer and usage are persisted; failures appear in
the evaluation and AI ledger; existing evaluation/permission/provider regressions remain passing.
## Plan
Replace the provider selection at the existing boundary without expanding the oversized runner.
Add endpoint-level success/failure regressions and document provider purpose and baseline limits.
## Verification
Fail regressions on original code; run evaluation and model configuration suites, lint and gates.
Rebuild the local API and check the mock evaluation path without any real model credentials.
## Risks
Configured real providers may charge; tests must stub network transport. Other baseline metrics
remain incomplete and must not be represented as production-quality measurements.
## Progress
2026-09-07: reproduced both success/failure configured-provider bypass cases; routed via shared provider.
25 evaluation/model-config tests passed. Final success/failure regressions also verify that a
non-member receives workspace_not_found before any extra provider call. Final lint passed.
The rebuilt API passed the browser evaluation/review journey (23.1 seconds).
Evidence: `.artifacts/20260907-evaluation-provider/`; all external transport was stubbed in tests.
## Decisions
Resolve the existing evaluation_direct_llm purpose rather than inventing a new API field.
## Findings
The RAG baseline and citation-presence groundedness metric remain separate known correctness gaps.
## Final Result
Completed for direct-baseline provider routing. Canned RAG answers, groundedness validity and
atomic spending controls remain open; this repair does not prove real-provider answer quality.
