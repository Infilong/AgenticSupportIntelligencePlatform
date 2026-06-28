# Operational Evaluation Expectations

## Goal
Make evaluations prove operational AI workflow behavior, not only answer text quality, by scoring expected tool calls and expected guardrail failures from stored LangGraph trace data.

## Context
The evaluation runner already measures pass rate, route accuracy, citation accuracy, groundedness, language preservation, latency, token use, and cost. It does not yet let JSONL cases assert that `system_v1` used required tools or triggered expected guardrail failures. This weakens the portfolio story because companies care whether agents are inspectable, governed, and tool-correct.

## Requirements
- Extend JSONL evaluation cases with optional `expected_tool_calls`.
- Extend JSONL evaluation cases with optional `expected_guardrail_failures`.
- For system-v1 runs, compare expected tool calls with stored `ToolCall` rows from the graph trace.
- For system-v1 runs, compare expected guardrail failures with stored `GuardrailResult` rows where `passed=false`.
- Store operational scores in `EvaluationResult.scores_json`.
- Aggregate operational metrics by mode and language.
- Show these metrics in the evaluation dashboard without hiding them behind the first four metrics.

## Non-goals
- Do not redesign the LangGraph workflow.
- Do not add LLM-as-judge evaluation.
- Do not add new database tables.
- Do not require real OpenAI calls in tests.

## Design Plan
- Add fields to `LoadedEvaluationCase` and parse JSONL keys.
- Persist declared operational expectations in case metadata for auditability.
- Collect actual tool names from `trace.steps[*].tool_calls` during system-v1 evaluation.
- Query failed guardrail results for the graph run during system-v1 evaluation.
- Add `tool_call_match` and `guardrail_failure_match` scores.
- Add `tool_call_correctness` and `guardrail_failure_detection_rate` metrics.
- Update dashboard metric ordering/grouping so operational metrics are visible.

## Test Plan
- Unit test JSONL loader parses the new optional fields.
- Unit test metric calculation includes operational metrics.
- API test runs system-v1 evaluation with expected tool calls and guardrail failures and verifies scores/metrics.
- Run backend lint/tests and frontend build.

## Risks
- Direct LLM and vector-only baselines will not have tool calls or guardrail traces; expectations should score as failed there when explicitly required.
- Guardrail names must match stored runtime guardrail types exactly.
- The dashboard should show more metrics without becoming noisy.

## Acceptance Criteria
- Evaluation JSONL can assert tool and guardrail behavior.
- Results record actual operational evidence in scores.
- Metrics expose tool correctness and guardrail failure detection.
- Tests prove the feature without real model calls.

## Human Review Checklist
- Check that JSONL examples are understandable.
- Check dashboard metric names are interview-explainable.
- Verify operational metrics are not confused with answer-quality metrics.

## Interview Notes
This shows that agent evaluation is not just output grading. The platform evaluates whether the workflow used the expected tools and whether governance controls fired when risky input required them.
