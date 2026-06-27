# Milestone 1: Project Skeleton

## Goal
Create a runnable local project skeleton that proves the repository can boot backend, frontend, PostgreSQL with pgvector, Redis, tests, linting, and CI without implementing product features yet.

This milestone establishes the development foundation for later AI/backend work. It must be boring, reliable, and easy to run.

## Context
Relevant docs:
- `AGENTS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/README.md`
- `docs/PLANS.md`
- `docs/product-spec.md`
- `docs/milestone-plan.md`
- `docs/architecture.md`
- `docs/api-design.md`

Milestone 1 deliverables from `docs/milestone-plan.md`:
- backend FastAPI app
- frontend skeleton
- Docker Compose
- PostgreSQL
- Redis
- pgvector extension setup
- pytest setup
- ruff setup
- health endpoint
- Makefile
- GitHub Actions CI

## Requirements
- Create a `backend/` FastAPI application with a minimal app factory or app module.
- Add `GET /health` returning a stable JSON response such as `{ "status": "ok", "service": "api" }`.
- Add backend dependency management with `pyproject.toml`.
- Add pytest setup and at least one backend test for `/health`.
- Add ruff configuration and a runnable lint command.
- Add a `frontend/` TypeScript skeleton using a simple React or Next.js setup.
- Add a minimal frontend page that identifies the product and does not pretend feature screens exist.
- Add Dockerfiles for backend and frontend if needed by Compose.
- Add `docker-compose.yml` with services for backend, frontend, PostgreSQL with pgvector, and Redis.
- Add PostgreSQL initialization for the `vector` extension.
- Add `.env.example` with local development variables only.
- Add `Makefile` targets for setup, run, test, lint, and formatting/checks where practical.
- Add GitHub Actions CI for backend tests/lint and frontend install/build checks.
- Update `README.md` local setup commands to match the actual skeleton.

## Non-goals
- No auth implementation.
- No user, workspace, or product database models.
- No Alembic migrations beyond optional empty scaffolding.
- No RAG, LangChain, LangGraph, token accounting, AI run ledger, or model provider implementation.
- No real OpenAI/Gemini/local model calls.
- No frontend product dashboards beyond a minimal skeleton page.
- No cloud deployment, Terraform, Kubernetes, or BigQuery.
- No seed/demo data yet.

## Design Plan
Use a monorepo layout:

```text
backend/
  app/
    main.py
    core/config.py
    api/health.py
  tests/test_health.py
  pyproject.toml
  Dockerfile
frontend/
  package.json
  tsconfig.json
  src or app files
  Dockerfile
infra/postgres/init/001_enable_pgvector.sql
docker-compose.yml
Makefile
.env.example
.github/workflows/ci.yml
```

Backend:
- Use FastAPI for the API skeleton.
- Use Pydantic settings or a small config module for environment variables.
- Keep `/health` intentionally dependency-light so it can confirm the API process is alive.
- Do not add product modules until their milestones.

Database and Redis:
- Use the `pgvector/pgvector` PostgreSQL image so `CREATE EXTENSION vector;` works locally.
- Include Redis as an available service but do not build worker logic yet.
- Define environment variables through `.env.example` and Compose defaults.

Frontend:
- Prefer a minimal TypeScript React/Next.js skeleton with a simple internal-product landing surface.
- Avoid building dashboard screens before their milestone.

CI:
- Run backend lint and tests.
- Run frontend install and build/type checks.
- Keep CI minimal and fast.

## Files Likely To Change
New files/directories:
- `backend/`
- `frontend/`
- `infra/postgres/init/001_enable_pgvector.sql`
- `docker-compose.yml`
- `Makefile`
- `.env.example`
- `.github/workflows/ci.yml`

Updated files:
- `README.md`
- possibly `.gitignore`
- possibly `docs/learning/fastapi-architecture.md` or a Milestone 1 learning note after implementation

## Database Migrations
No application tables in this milestone.

Database setup only:
- Create a local development database through Docker Compose.
- Enable the `vector` extension through an init SQL script.

If Alembic scaffolding is added, it must contain no product schema yet.

## API Changes
Add one public endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "api"
}
```

No authenticated or workspace-scoped APIs in this milestone.

## Test Plan
Backend unit/API tests:
- `GET /health` returns HTTP 200.
- Response body contains stable `status` and `service` fields.

Lint/checks:
- `ruff check backend` or equivalent passes.
- frontend type/build command passes.

Manual tests:
- `docker compose up --build` starts backend, frontend, PostgreSQL, and Redis.
- `curl http://localhost:<backend_port>/health` returns OK.
- frontend loads in browser.

CI:
- GitHub Actions runs backend tests and lint.
- GitHub Actions runs frontend install and build/type checks.

## Acceptance Criteria
- `docker compose up --build` starts all Milestone 1 services.
- `GET /health` returns OK from the running backend container.
- backend tests pass locally.
- backend lint command exists and passes.
- frontend build/type command exists and passes.
- CI workflow exists and runs the same basic checks.
- README local setup section matches the actual commands.
- No application feature code beyond skeleton/health exists.

## Risks
- Overbuilding: adding auth, models, RAG, LangGraph, or AI provider abstractions too early.
- Fake completeness: creating placeholder modules that imply product behavior exists when it does not.
- Dependency sprawl: adding AI libraries before they are needed.
- Docker drift: local commands work but Compose or CI does not.
- pgvector setup failure if the wrong PostgreSQL image is used.
- Frontend scope creep into dashboard design before backend foundations exist.

## Human Review Checklist
- Confirm the diff is only skeleton infrastructure.
- Confirm no product features are implemented early.
- Confirm `/health` is simple and tested.
- Confirm Docker Compose is understandable and not overbuilt.
- Confirm pgvector extension setup is real, not a comment-only placeholder.
- Confirm README commands work as written.
- Confirm CI does not require secrets or real AI provider credentials.

## Operating Notes
After implementation, update or create a learning note explaining:
- why FastAPI is used for the backend skeleton
- why Docker Compose is used for local-first development
- why pgvector is introduced early but product tables are deferred
- how to explain the skeleton in a portfolio/interview context

Codex self-review after implementation must focus on:
- accidental scope creep
- missing tests
- unreliable Docker setup
- misleading placeholders
- commands that are documented but not verified
