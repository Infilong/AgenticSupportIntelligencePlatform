# Ticket Planning Protocol

This file is an execution-plan template for long tasks. It is not the product plan.

The project plan lives in:
- `docs/product-spec.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/milestone-plan.md`
- `docs/architecture.md`

Use this template before implementing any non-trivial ticket. Do not code complex changes before a plan is approved.

```text
# Ticket Title

## Goal
What are we trying to build or change?

## Context
Which modules, files, docs, or prior decisions matter?

## Requirements
Concrete behavior.

## Non-goals
What this ticket must not do.

## Design Plan
Expected files/modules/tables/APIs.

## Files Likely To Change
List expected files or directories. Keep this focused.

## Database Migrations
Tables, columns, indexes, constraints, and ownership rules.

## API Changes
Routes, request/response shapes, auth requirements, and error cases.

## Test Plan
Unit tests, integration tests, manual tests.

## Acceptance Criteria
What must be true before the ticket is complete?

## Risks
Possible mistakes, edge cases, security risks, performance issues.

## Human Review Checklist
What should the human inspect before accepting the diff?

## Operating Notes
What should be documented or reviewed after this ticket?
```

## Required Ticket Workflow
1. Read relevant docs first.
2. Create a focused plan using this template.
3. Wait for approval on complex work.
4. Implement only the approved scope.
5. Add tests.
6. Run relevant validation commands.
7. Explain the diff.
8. Self-review for P0/P1/P2 issues.
9. Update docs or learning notes where relevant.

## Review Focus
Check every implementation for workspace permission leaks, fake implementation, missing tests, hidden model calls in tests, raw documents sent to LLMs, missing token/cost tracking, missing graph trace data, weak error handling, prompt injection exposure, and unclear project rationale.
