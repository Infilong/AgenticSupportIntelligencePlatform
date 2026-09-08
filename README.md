# Multilingual Support Workbench

Fresh rebuild on `codex/fresh-start`. **M0 preparation only: no product application exists yet.**
The scoped product is a local EN/JA/ZH support workbench using LangChain, LangGraph and
PostgreSQL/pgvector, with one worker and no Redis or cloud platform.

- [Release plan and topology](REBUILD_PLAN.md)
- [Current status and next step](docs/STATUS.md)
- [Acceptance gates](docs/ACCEPTANCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Preparation runbook](docs/RUNBOOK.md)

## Verify M0

From the repository root with Python 3.12+, Node.js 22+, npm, uv, Git and Docker Desktop:

```text
python scripts/manage.py doctor
python scripts/manage.py verify-prep
python scripts/manage.py verify-browser
python scripts/manage.py evidence
```

For first-time Playwright installation, follow the [runbook](docs/RUNBOOK.md).
The browser command tests an environment probe; it does not demonstrate the planned app.
Evidence lives under `.artifacts/m0/` and is intentionally excluded from Git.

`up`, `migrate`, `seed-demo`, `verify-live`, backup and restore commands will be implemented
with their owning milestones. They are not available now. Do not start the archived app as
proof of this rebuild. API spending is zero until explicitly authorized.

The previous implementation and history remain on `archive/previous-platform-2026-09-08`.
This branch will not import its database or reuse its dependencies automatically.
