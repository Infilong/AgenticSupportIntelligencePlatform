# Documentation guidance

Scope: this directory; also read for root Markdown changes. Read the [root director](../AGENTS.md).

- Keep one owner per fact: [release plan](../REBUILD_PLAN.md) for scope/topology,
  [architecture](ARCHITECTURE.md) for design, [acceptance](ACCEPTANCE.md) for gates,
  [runbook](RUNBOOK.md) for commands, [status](STATUS.md) for current evidence/next action,
  and [development](DEVELOPMENT.md) for the execution protocol.
- Keep the root `AGENTS.md` a short director. Put area-specific instructions in that area's
  `AGENTS.md`; link deeper design or recipes instead of expanding always-read context.
- Keep each instruction file under 200 lines. Add local guides as real responsibilities
  appear, not an instruction file for every folder. Keep links and ownership clear.
- Guides describe how to work; they are not permission to start another milestone.
- Mark planned, implemented and verified behavior explicitly. Never infer readiness from
  documentation, a configured command or the existence of a test file.
- Use stable revision references and exact evidence paths; retain failures and limitations.
- Check relative links and review documentation diffs. For preparation contract changes,
  run the existing preparation checks described in [runbook](RUNBOOK.md).
