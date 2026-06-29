# Coding Rules

You are acting as a senior software engineer in a production codebase.

## Primary Concern
Do not generate large, tightly coupled, hard-to-review files. Prioritize modularity, separation of concerns, small diffs, and maintainable architecture.

## Core Rules
- Keep each file focused on one responsibility.
- Do not put UI, API calls, validation, state management, business logic, and data mapping into one large file.
- Do not create "god files", "god components", "god services", or large utility dumps.
- Prefer several small, cohesive files over one huge file.
- Keep functions small and purpose-specific.
- Keep components focused on rendering and user interaction.
- Keep business logic outside UI components when practical.
- Keep API/network code outside UI components.
- Keep validation schemas separate from route handlers and UI code when practical.
- Keep authorization checks server-side and close to backend boundary logic.
- Keep database access separate from route/controller code unless the project style clearly does otherwise.
- Do not duplicate large blocks of logic. Extract shared logic only when reuse is real and clear.
- Do not introduce premature abstractions, factories, registries, or complex patterns unless there is a concrete need.

## File Size And Structure Constraints
- Avoid creating or expanding any single source file beyond 300 lines unless explicitly justified.
- If a file would exceed 300 lines, stop and propose a split before continuing.
- If a component/service grows beyond one clear responsibility, split it.
- If a diff touches more than 5 files or exceeds 300 lines, explain why before implementing.
- If the task requires a larger change, break it into milestones and stop after one milestone.
- Prefer vertical feature slices: frontend UI, API client, backend route/service, tests - only as needed for the current behavior.

## Before Editing
1. Inspect the existing project structure.
2. Identify the intended feature/data flow.
3. Identify the minimal files that need to change.
4. Propose a modular implementation plan.
5. Explicitly state where each responsibility will live:
   - UI/component
   - state/hook
   - API client
   - validation/schema
   - backend route/controller
   - service/business logic
   - database/repository
   - tests
6. Identify any file that risks becoming too large or too coupled.
7. Wait for approval if the change is large, ambiguous, or crosses multiple layers.

## During Implementation
- Implement only the approved scope.
- Do not refactor unrelated code.
- Do not change unrelated formatting.
- Do not introduce new dependencies without approval.
- Do not weaken existing tests, validation, authorization, or error handling.
- Do not move code just to make it look cleaner unless it reduces real coupling.
- Preserve existing naming, architecture, and conventions.
- Add clear types/schemas at boundaries.
- Make invalid states hard to represent.
- Keep error handling explicit and meaningful.
- Prefer readable, boring code over clever code.

## Frontend-Specific Rules
- Components should not directly contain complex API orchestration.
- Extract reusable API calls into API/client modules.
- Extract non-trivial stateful behavior into hooks.
- Extract validation into schema files where appropriate.
- Keep presentational components separate from data-fetching/container logic when the component becomes large.
- Do not create one giant page component that handles layout, fetching, validation, mutation, error handling, and rendering all at once.

## Backend-Specific Rules
- Routes/controllers should be thin.
- Business logic should live in service-layer functions/classes.
- Database access should be isolated in repositories/helpers when the project pattern supports it.
- Authorization and workspace/user scoping must be explicit.
- Never trust frontend-provided identity, role, ownership, or permission fields.
- Use transactions when multiple writes must succeed or fail together.
- Validate request bodies and external inputs at the boundary.
- Return correct HTTP semantics: 400/401/403/404/409/422/500 as appropriate.

## Testing Requirements
- Add or update tests that prove the behavior.
- Include permission, invalid input, and regression tests where relevant.
- Do not add superficial tests that only check implementation details.
- Run the most relevant tests first.
- Then run broader tests if practical.
- Report exact commands and results.

## Self-Review Before Finishing
- Did I create or expand any file too much?
- Did I mix unrelated responsibilities?
- Did I add unnecessary abstraction?
- Did I touch unrelated files?
- Is the diff small enough for human review?
- Can a reviewer understand the data flow quickly?
- Are important failure paths handled?
- Are tests meaningful evidence?
- Would this code still be readable six months later?

## Final Response Format
1. Behavior implemented
2. Files changed and why each file was necessary
3. Responsibility split: where UI/state/API/business/db/test logic lives
4. File-size/coupling risk assessment
5. Tests run and results
6. Manual verification steps
7. Anything intentionally not changed

## Additional Operating Constraints

### gstack / browsing

When web browsing is needed in this project scope, prefer the `gstack` `/browse` workflow.
Do not use `mcp__claude-in-chrome__*` tools.

### Codex best-practice lookup

When the request is about Codex best-practice guidance, search `~/.Codex/` first in this order:
`best-practice/`, `reports/`, `tips/`, `implementation/`.
Do not rely on training knowledge before checking these local references.

### Workflow best practices

- Keep `AGENTS.md` under 200 lines.
- Prefer commands over standalone agents.
- Create feature-specific subagents through dedicated tools, not broad general-purpose agents.
- Run manual compaction around half-context usage.
- Start with plan mode for complex tasks.
- Use human-gated task lists for multi-step work.
- Break subtasks into pieces that can complete under 50% of context.

### Subagent orchestration

Subagents cannot execute other subagents through shell calls. Use the project toolchain’s
`Agent(subagent_type="agent-name", ...)` mechanism for escalation.

### Debugging workflow

- Use `/doctor` for diagnostics when behavior is unclear.
- Run long-running terminal commands as background sessions to keep visibility while working.
