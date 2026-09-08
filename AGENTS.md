# Repository director

## Authority

- Follow the current user-authorized scope and [status](docs/STATUS.md); stop at its boundary.
- [REBUILD_PLAN.md](REBUILD_PLAN.md) owns product scope. The archived implementation is historical.
- Use only OpenAI-provided Codex tools and skills; no custom or third-party skill bundles.
- Preserve unrelated work, archived data and secrets. Commit and push small verified steps
  to the working branch; merges, deployment and paid API use require separate authority.

## Route the task

Read [development workflow](docs/DEVELOPMENT.md), then only the guides relevant to the task.
Before editing a directory, read its local `AGENTS.md` and any deeper applicable guide.

| Work area | Local instructions |
| --- | --- |
| Frontend and browser journeys | [frontend/AGENTS.md](frontend/AGENTS.md) |
| Backend, database, retrieval and agent execution | [backend/AGENTS.md](backend/AGENTS.md) |
| Evaluation cases and policy corpus | [evals/AGENTS.md](evals/AGENTS.md) |
| Developer commands and evidence | [scripts/AGENTS.md](scripts/AGENTS.md) |
| Runtime configuration and deployment | [infra/AGENTS.md](infra/AGENTS.md) |
| Plans, contracts and documentation | [docs/AGENTS.md](docs/AGENTS.md) |

Shared references: [architecture](docs/ARCHITECTURE.md),
[acceptance gates](docs/ACCEPTANCE.md), [commands and recovery](docs/RUNBOOK.md).

## Coordinate and finish

- Own the closed loop: demand → assess → write execution prompt → implement → verify/review
  → repair or select the next authorized slice. Follow [the protocol](docs/DEVELOPMENT.md).
- Do not require the user to write technical prompts or repeatedly say “continue” within
  an authorized goal. A generated prompt cannot expand that goal or grant new authority.
- Turn each nontrivial request, including reviews and planning, into a concise execution brief
  before acting. Preserve the user's intent; resolve routine details without asking for a new prompt.
- Keep one implementation owner per slice. Delegate bounded read-only investigation/review when useful.
- Give each spawned agent its goal, owned paths, applicable guide paths, acceptance criteria
  and expected evidence. Require it to read those guides and preserve other agents' work.
- Integrate and review delegated results; the coordinating agent owns the final verification.
- Update the owning documents and status; report verified, failed, skipped and unverified results.
- Keep this file a concise director, without implementation details or command recipes.
  Each substantive area must maintain its own short `AGENTS.md`; add deeper guides only
  when distinct responsibilities justify them. Link details instead of copying them here.
