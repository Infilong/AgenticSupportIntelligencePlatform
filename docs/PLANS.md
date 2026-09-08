# Persistent execution plans

Create a plan only for cross-cutting, long-running, architecture-sensitive, security-sensitive,
or multi-session work. Simple scoped changes need a brief working plan and relevant checks,
not a new Markdown file. Product scope stays in [product spec](product-spec.md) and
[milestones](milestone-plan.md); operational sequencing lives in execution plans.

Create `docs/exec-plans/active/<topic>.md`, using the template below. Keep the plan self-contained
through links to authoritative context, not copied manuals. Identify ownership, API/schema/
migration effects, compatibility and rollback where relevant. Plan first for high-risk work;
request approval only for decisions or actions outside existing authorization.

When resuming, read the latest user request before selecting an active plan. A plan records
execution history and remaining work; it does not grant authority or override a narrower current
request. Recheck the worktree and saved evidence before relying on its status. Leave broader
plans active while completing a scoped documentation, review or investigation request.

```markdown
# Title
## Goal
Required outcome.
## Context
Relevant code, docs, prior decisions and current evidence.
## Requirements
Concrete contracts and constraints.
## Non-goals
Explicit exclusions.
## Acceptance Criteria
Observable conditions, including denied and failed operations where relevant.
## Plan
Ordered small steps and ownership/files for each responsibility.
## Verification
Commands, test boundaries, expected results and evidence paths.
## Risks
Security, concurrency, data integrity, compatibility and rollback considerations.
## Progress
Dated completed/current steps and verified process handles when work is running.
## Decisions
Dated choices with reasons; retain superseded decisions as history.
## Findings
Reproductions, failures, surprises and resulting next actions.
## Final Result
Open until acceptance is verified; then exact outcome and remaining limits.
```

Update Progress, Decisions and Findings at meaningful checkpoints. Preserve failing evidence;
never replace a failed run with a success claim from a narrower retry. Record durable learning
using [learning notes](learning/README.md) when useful.

Move a plan to `completed/` only after its acceptance criteria are met; update inbound links and
[the plan index](exec-plans/README.md). A blocked plan remains active with its blocker and next
required action. Historical `docs/tickets/` files remain linked evidence; do not mass-relocate or
mark them complete without inspecting their acceptance criteria.
