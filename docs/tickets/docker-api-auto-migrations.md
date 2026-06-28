# Docker API Auto Migrations

## Goal
Prevent local Docker deployments from serving stale database schemas after new Alembic migrations are added.

## Context
Browser smoke testing exposed a live schema drift problem: the API container restarted with code that expected `agent_configs.folder_id`, but the PostgreSQL volume was still at an earlier Alembic revision. The immediate manual fix was `cd backend && uv run alembic upgrade head`, but a local-first portfolio app should make `docker compose up` safer by applying migrations before serving the API.

## Requirements
- Include Alembic migration files in the backend runtime image.
- Run `alembic upgrade head` before `uvicorn` starts.
- Keep the change scoped to the Docker local deployment path.
- Preserve `uv` as the Python package manager.

## Implementation
- Updated `backend/Dockerfile` to copy `alembic.ini` and `alembic/` into the image.
- Changed the container command to run `alembic upgrade head && uvicorn ...`.

## Verification
- `docker compose up -d --build api` rebuilt and restarted the API image.
- API startup logs showed Alembic migration context before Uvicorn startup.
- `curl -fsS http://127.0.0.1:8000/health` returned OK after startup settled.
- `make frontend-e2e-docker` passed after the API auto-migration startup change.

## Risks
- This is appropriate for the local Docker Compose deployment. A production Cloud Run path should use an explicit migration job or deployment step rather than running migrations from every horizontally scaled API instance.

## Interview Notes
Explain this as deployment integrity: professional backend systems must keep code and schema in sync. The local portfolio path now demonstrates automatic migration on startup, while the scale-path remains honest about using a separate migration job in production.
