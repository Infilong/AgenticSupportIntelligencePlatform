# Milestone 8: Guardrails And Human Review

## What Was Built
Milestone 8 added deterministic guardrails and a real human review workflow:
- `GuardrailResult` and `HumanReview` tables.
- prompt-injection, citation-required, unsupported-answer, confidence-threshold, and language-preservation checks.
- guardrail evaluation after graph runs.
- blocking guardrails route runs to `needs_human_review`.
- pending review creation.
- review list/detail/resolve APIs.
- tests for review creation, prompt injection, resolution, and workspace isolation.

## Why Companies Care
AI systems need operational fallback paths. Human review protects users and companies when the system lacks evidence, detects injection, or has low confidence. Guardrail records make these decisions auditable instead of hidden inside application logic.

## How This Project Uses It
After a LangGraph run completes, deterministic guardrails evaluate the state. If evidence is missing, citations are absent, confidence is low, or prompt injection is detected, the graph run is marked as needing human review and a pending review record is created.

## Design Tradeoffs
- Deterministic guardrails are cheap, fast, and testable, but not comprehensive safety classifiers.
- Review resolution is backend-only for now; frontend review UI is Milestone 10.
- Guardrails run after graph execution in v1, keeping LangGraph node changes small and inspectable.
- Prompt injection detection uses pattern matching and should later be strengthened with policy/rubric evaluation.

## Failure Modes
- Overly broad prompt-injection patterns can create false positives.
- Weak no-source thresholds can still allow unsupported answers before guardrails catch them.
- Review APIs must always filter by workspace.
- Human review should not become only a status flag; it needs reviewer, decision, edited answer, and comments.

## Interview Explanation
“I added deterministic guardrails and human review as an operational safety layer. The graph still runs as an inspectable workflow, then guardrails evaluate evidence, citations, confidence, language preservation, and injection patterns. Blocking failures create persisted guardrail records and a pending human review. This makes unsupported cases auditable and gives the product a real fallback path.”

## Review Checklist
- Verify blocking guardrails create human reviews.
- Verify prompt injection routes to review.
- Verify review resolve cannot be repeated.
- Verify review access is workspace-scoped.
- Verify deterministic guardrail limitations are documented.
