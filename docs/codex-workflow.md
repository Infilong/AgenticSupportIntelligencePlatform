# Codex Workflow

This project must be built using an AI-native engineering workflow. Codex must not try to implement the entire platform in one large step.

## Working Loop
1. Plan.
2. Create or update architecture docs.
3. Break work into tickets.
4. Implement one small ticket.
5. Add tests.
6. Run validation commands.
7. Explain the diff.
8. Update learning notes and docs.
9. Review design tradeoffs.
10. Stop for human review before the next ticket.

## Human Role
The human engineer owns requirements, scope decisions, architecture approval, code review, test review, final merge decisions, project narrative, and quality bar.

## Codex Role
Codex assists with planning, boilerplate, implementation, tests, debugging, docs, refactoring, code review, and explaining code.

## Ticket Workflow

### Step A: Planning Prompt
```text
Read the current repository and relevant docs.

Do not edit files yet.

Create a ticket plan for [FEATURE NAME] using docs/PLANS.md.

Include:
1. goal
2. context
3. requirements
4. non-goals
5. design plan
6. files likely to change
7. database migrations
8. API changes
9. test plan
10. risks
11. acceptance criteria
12. human review checklist
13. operating notes

Wait for my approval before implementing.
```

### Step B: Implementation Prompt
```text
Implement the approved ticket plan.

Constraints:
- keep the diff focused
- do not add unrelated refactors
- add tests
- update docs only where relevant
- use mock LLM/embedding providers in tests
- enforce workspace permissions
- run relevant tests and report results

When finished, provide:
1. changed files
2. design summary
3. test results
4. known limitations
5. what I should review manually
```

### Step C: Review Prompt
```text
Review your own diff as if you are a senior backend/AI platform engineer.

Focus on:
- architecture consistency
- workspace permission leaks
- fake or superficial implementations
- missing tests
- error handling
- token/cost tracking
- RAG quality
- LangGraph traceability
- security
- maintainability

Do not edit files yet.
List P0/P1/P2 issues.
```

### Step D: Fix Prompt
```text
Fix only the P0/P1 issues from the review.

Do not refactor unrelated code.
Add or update tests proving the fix.
Run the relevant validation commands.
Explain the changes.
```

### Step E: Learning Prompt
```text
Create or update a learning note in docs/learning/ for this milestone.

The note should explain:
1. what was built
2. why companies care
3. how this project uses the concept
4. design tradeoffs
5. failure modes
6. how this should be explained in project documentation
```

## Advanced Codex Methods To Practice
- Plan-first mode for architecture, database design, LangGraph workflows, evaluation, security, and major features.
- Ticket decomposition into reviewable units.
- Context files: `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/PLANS.md`, design docs, and learning notes.
- Diff review loop after implementation.
- Test-first or test-aware development for permissions, token budget, retrieval, evaluation, graph routing, and guardrails.
- Mock providers for LLM responses, embeddings, token counts, latency simulation, and error simulation.
- Red-team prompts to attack workspace isolation, guardrails, raw document leakage, and human-review bypass.
- Architecture consistency reviews after each milestone.
- Decision and tradeoff extraction after each milestone.
- Parallel Codex tasks only when they modify separate files or modules.
- PR-style workflow with summary, tests, screenshots if UI, limitations, checklist, and self-review.
- Local verification by the human when possible: `docker compose up`, `pytest`, `ruff check .`, `npm test`, `npm run build`.
