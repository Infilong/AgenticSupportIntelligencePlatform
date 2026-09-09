# Multilingual Support Workbench

Fresh rebuild on `codex/fresh-start`. Foundation and knowledge ingestion/search UI exist.
The connected workbench processes messages into cited development drafts, exposes sources and
processing records, and supports cancellation and attributable approve/edit/reject/clarify decisions.
Administrators can record a clarification question without approving or sending the draft.
Linked retries and customer clarifications preserve original messages and attempt history.
Inbox views separate messages needing attention, approved responses, processing and failures.
Linked-attempt database/browser checks pass; the full release gates remain unfinished.
See [current status](docs/STATUS.md)
for the milestone, execution boundary and dated verification evidence.
The scoped product is a local EN/JA/ZH support workbench using LangChain, LangGraph and
PostgreSQL/pgvector, with one worker and no Redis or cloud platform.

- [Current topology and data flow](docs/ARCHITECTURE.md#current-project-topology)
- [Release plan and target topology](REBUILD_PLAN.md#target-project-topology)
- [Current status and next step](docs/STATUS.md)
- [Acceptance gates](docs/ACCEPTANCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [RAG design, audit and failure contract](docs/RAG.md)
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
For the packaged local app, use `release-up`, `release-seed` and `release-prepare-model`;
open `http://127.0.0.1:8011`. It serves built assets from FastAPI and has separate database/model
volumes. [The runbook](docs/RUNBOOK.md#built-local-release) explains setup and verification.
`verify-restore` creates a fresh backup snapshot, restores a new disposable database, checks
table fingerprints and exercises the restored API/worker. It preserves the source and existing
databases. `backup` exports the isolated development database without creating a restore clone;
see the [backup runbook](docs/RUNBOOK.md#standalone-development-database-backup) for scope and limits.
`verify-restore --backup-dir .artifacts/m6/backup-<timestamp>` checks a trusted saved backup in a
new disposable database without replacing current data.
`verify-live` remains unimplemented; no external
generation has been verified. Do not use the archived app as proof of this rebuild.
API spending is zero until explicitly authorized.

The previous implementation and history remain on `archive/previous-platform-2026-09-08`.
This branch will not import its database or reuse its dependencies automatically.
