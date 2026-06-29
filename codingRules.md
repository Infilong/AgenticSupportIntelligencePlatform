# codingRules

These are mandatory process and coding rules for this project.

## Browser and Tooling
- Use `/browse` from **gstack** for all web browsing.
- Never use `mcp__claude-in-chrome__*` tools.
- Available gstack skills:
  - `/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`,
    `/design-consultation`, `/design-shotgun`, `/design-html`,
    `/review`, `/ship`, `/land-and-deploy`, `/canary`, `/benchmark`,
    `/connect-chrome`, `/qa`, `/qa-only`, `/design-review`, `/setup-browser-cookies`,
    `/setup-deploy`, `/retro`, `/investigate`, `/document-release`, `/codex`, `/cso`,
    `/autoplan`, `/careful`, `/freeze`, `/guard`, `/unfreeze`, `/gstack-upgrade`, `/learn`.

## Codex best-practice questions
- When asking a Codex best-practice question, always search `~/.Codex/` first in:
  - `best-practice/`
  - `reports/`
  - `tips/`
  - `implementation/`

## Workflow best practices
- Keep `AGENTS.md` under 200 lines.
- Use commands for workflows instead of standalone agents.
- Create feature-specific subagents with skills (progressive disclosure), not broad purpose.
- Perform manual `/compact` around ~50% context usage.
- Start with plan mode for complex tasks.
- Use human-gated task list workflow for multi-step tasks.
- Break subtasks so each is small enough to complete under 50% context usage.

## Subagent orchestration
- Subagents cannot invoke other subagents via shell commands.
- Use the Agent tool with:
  - `Agent(subagent_type="agent-name", description="...", prompt="...", model="haiku")`

## Debugging tips
- Use `/doctor` for diagnostics.
- Run long-running terminal commands as background tasks for better log visibility.

## Environment reminder
- Repository path: `/home/infilong/project/AgenticSupportIntelligencePlatform`.
- Always keep and consult these rules during planning, implementation, and reviews.

## Primary architecture and code size constraints
- You are acting as a senior software engineer in a production codebase.
- Primary concern: Do not generate large, tightly coupled, hard-to-review files. Prioritize modularity, separation of concerns, small diffs, and maintainable architecture.

### Core rules
- Keep each file focused on one responsibility.
- Do not put UI, API calls, validation, state management, business logic, and data mapping into one large file.
- Do not create god files, god components, god services, or large utility dumps.
- Prefer several small, cohesive files over one huge file.
- Keep functions small and purpose-specific.
- Keep components focused on rendering and user interaction.
- Keep business logic outside UI components when practical.
- Keep API/network code outside UI components.
- Keep validation schemas separate from route handlers and UI code when practical.
- Keep authorization checks server-side and close to backend boundary logic.
- Keep database access separate from route/controller code unless project style clearly uses co-location.
- Do not duplicate large blocks of logic. Extract shared logic only when reuse is real and clear.
- Do not introduce premature abstractions, factories, registries, or complex patterns unless there is a concrete need.

### File size and structure constraints
- Avoid creating or expanding any single source file beyond 300 lines unless explicitly justified.
- If a file would exceed 300 lines, split it before continuing.
- If a component/service grows beyond one clear responsibility, split it.
- If a diff touches more than 5 files or exceeds 300 lines, explain why before implementing.
- If the task requires larger change, break into milestones and stop after one milestone.
- Prefer vertical feature slices: frontend UI, API client, backend route/service, tests.

### Before editing
1. Inspect existing project structure.
2. Identify intended feature/data flow.
3. Identify minimal files to change.
4. Propose a modular implementation plan.
5. Explicitly state where each responsibility will live:
   - UI/component
   - state/hook
   - API/client
   - validation/schema
   - backend route/controller
   - service/business logic
   - database/repository
   - tests
6. Identify any file that risks becoming too large or too coupled.
7. Wait for approval if change is large, ambiguous, or crosses multiple layers.

### During implementation
- Implement only approved scope.
- Do not refactor unrelated code.
- Do not change unrelated formatting.
- Do not introduce new dependencies without approval.
- Do not weaken existing tests, validation, authorization, or error handling.
- Do not move code only for cosmetic cleanup unless it reduces real coupling.
- Preserve existing naming, architecture, and conventions.
- Add clear types/schemas at boundaries.
- Make invalid states hard to represent.
- Keep error handling explicit and meaningful.
- Prefer readable, boring code over clever code.

### Frontend rules
- Components should not directly contain complex API orchestration.
- Extract reusable API calls into API/client modules.
- Extract non-trivial stateful behavior into hooks.
- Extract validation into schema files where appropriate.
- Keep presentational components separate from container/data-fetching logic when component becomes large.
- Do not create one giant page component that handles layout, fetching, validation, mutation, and rendering all at once.

### Backend rules
- Routes/controllers should be thin.
- Business logic should live in service-layer functions/classes.
- Database access should be isolated in repositories/helpers when project pattern supports it.
- Authorization and workspace/user scoping must be explicit.
- Never trust frontend-provided identity/role/ownership/permission fields.
- Use transactions when multiple writes must succeed or fail together.
- Validate request bodies and external inputs at the boundary.
- Return correct HTTP semantics: 400/401/403/404/409/422/500 as appropriate.

### Testing requirements
- Add or update tests that prove the behavior.
- Include permission, invalid input, and regression tests where relevant.
- Do not add superficial tests that only check implementation details.
- Run the most relevant tests first, then broader tests if practical.
- Report exact commands and results.

### Self-review before finishing
- Did I create or expand any file too much?
- Did I mix unrelated responsibilities?
- Did I add unnecessary abstraction?
- Did I touch unrelated files?
- Is the diff small enough for human review?
- Can a reviewer understand the data flow quickly?
- Are important failure paths handled?
- Are tests meaningful evidence?
- Is this code readable six months later?

### Final response format
1. Behavior implemented
2. Files changed and why each file was necessary
3. Responsibility split: UI/state/API/business/db/test logic
4. File-size/coupling risk assessment
5. Tests run and results
6. Manual verification steps
7. Anything intentionally not changed
