# Multilingual Support Workbench

Fresh rebuild on `codex/fresh-start`. Foundation and knowledge ingestion/search UI exist.
The backend processes messages into cited development drafts; its workbench UI and human-review
flow remain unfinished. See [current status](docs/STATUS.md)
for the milestone, execution boundary and dated verification evidence.
The scoped product is a local EN/JA/ZH support workbench using LangChain, LangGraph and
PostgreSQL/pgvector, with one worker and no Redis or cloud platform.

- [Current topology and data flow](docs/ARCHITECTURE.md#current-project-topology)
- [Release plan and target topology](REBUILD_PLAN.md#target-project-topology)
- [Current status and next step](docs/STATUS.md)
- [Acceptance gates](docs/ACCEPTANCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Preparation runbook](docs/RUNBOOK.md)

## Preparation checks

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

For the isolated API/database, use `init-env`, then `up` from the [runbook](docs/RUNBOOK.md).
`up` starts the API, frontend, worker and PostgreSQL. `seed-demo` creates synthetic sign-in
accounts; follow the runbook for model preparation and actual knowledge journeys.
`verify-live`, backup and restore remain to implement. Do not start the archived app as
proof of this rebuild. API spending is zero until explicitly authorized.

The previous implementation and history remain on `archive/previous-platform-2026-09-08`.
This branch will not import its database or reuse its dependencies automatically.
