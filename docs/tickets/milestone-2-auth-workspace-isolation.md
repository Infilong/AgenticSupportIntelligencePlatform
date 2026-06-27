# Milestone 2: Auth And Workspace Isolation

## Goal
Build the first real backend product foundation: user registration/login, JWT authentication, workspace creation/listing/detail access, and a reusable workspace membership dependency that later features must use.

The main portfolio value is not login itself. The value is proving that every future dataset, document, retrieval, agent run, evaluation, and cost API has a clear permission boundary from the start.

## Context
Relevant docs:
- `AGENTS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/database-schema.md`
- `docs/api-design.md`
- `docs/security-threat-model.md`
- `docs/milestone-plan.md`
- `docs/PLANS.md`

Milestone 1 already provides:
- FastAPI backend skeleton
- Docker Compose with PostgreSQL, pgvector, and Redis
- `uv` backend workflow
- pytest and ruff
- `GET /health`

Milestone 2 should introduce database-backed auth and workspace isolation without adding downstream product modules early.

## Requirements
- Add SQLAlchemy-based persistence for users, workspaces, and workspace members.
- Add Alembic migrations for the auth/workspace tables.
- Add password hashing for stored credentials.
- Add JWT access token creation and verification.
- Add auth routes:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
- Add protected workspace routes:
  - `GET /api/v1/workspaces`
  - `POST /api/v1/workspaces`
  - `GET /api/v1/workspaces/{workspace_id}`
- Creating a workspace must also create an owner membership for the current user.
- Workspace detail access must require membership.
- Add reusable dependencies for current user and workspace membership checks.
- Use explicit 401 for missing/invalid auth and explicit 403/404 behavior for forbidden workspace access.
- Add tests proving auth works and cross-workspace access is denied.
- Keep `/health` public and dependency-light.

## Non-goals
- No frontend login UI yet.
- No OAuth, SSO, password reset, email verification, MFA, or refresh-token rotation.
- No complex role hierarchy beyond `owner` and `member`.
- No dataset, document, retrieval, LangGraph, AI run ledger, evaluation, or cost APIs.
- No audit log API yet.
- No real AI provider calls.
- No Redis session store; JWT verification is stateless in v1.

## Design Plan
Backend structure:

```text
backend/app/
  api/v1/
    router.py
    auth.py
    workspaces.py
  core/
    config.py
    security.py
  db/
    base.py
    session.py
  dependencies/
    auth.py
    workspace.py
  models/
    user.py
    workspace.py
  schemas/
    auth.py
    workspace.py
  services/
    auth_service.py
    workspace_service.py
backend/alembic/
backend/alembic.ini
```

Implementation choices:
- Use SQLAlchemy 2.x ORM.
- Use PostgreSQL in Docker/local runtime through `DATABASE_URL`.
- Use SQLite only for isolated tests if it keeps tests fast and does not hide permission logic; permission-sensitive behavior must be covered at service/API level.
- Use UUID primary keys for users and workspaces.
- Normalize emails to lowercase before uniqueness checks.
- Hash passwords; never store or log plaintext passwords.
- JWT payload should include `sub` as the user ID and an expiration.
- Add `JWT_SECRET_KEY`, `JWT_ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES` to settings and `.env.example`.
- Use a central `get_current_user` dependency for protected routes.
- Use a central `require_workspace_member` dependency for any route with `workspace_id`.

Tables:
- `users`
- `workspaces`
- `workspace_members`

Indexes/constraints:
- `users.email` unique.
- `workspace_members(workspace_id, user_id)` unique.
- Foreign keys from `workspaces.created_by_user_id` and `workspace_members`.

Error handling:
- Invalid credentials return 401 with a stable error code.
- Missing bearer token returns 401.
- Invalid/expired token returns 401.
- Non-member workspace access returns 404 or 403 consistently; prefer 404 to avoid confirming workspace existence unless the API design later standardizes on 403.

## Files Likely To Change
- `backend/pyproject.toml`
- `backend/uv.lock`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/db/`
- `backend/app/api/v1/`
- `backend/app/dependencies/`
- `backend/app/models/`
- `backend/app/schemas/`
- `backend/app/services/`
- `backend/tests/`
- `backend/alembic.ini`
- `backend/alembic/`
- `.env.example`
- `README.md` only if setup/migration commands change
- `docs/learning/milestone-2-auth-workspace-isolation.md`

## Database Migrations
Create one Alembic migration for:

```text
users
- id UUID primary key
- email text unique not null
- password_hash text not null
- display_name text not null
- created_at timestamptz not null

workspaces
- id UUID primary key
- name text not null
- created_by_user_id UUID not null references users(id)
- created_at timestamptz not null

workspace_members
- id UUID primary key
- workspace_id UUID not null references workspaces(id) on delete cascade
- user_id UUID not null references users(id) on delete cascade
- role text not null
- created_at timestamptz not null
- unique(workspace_id, user_id)
```

Do not create product-owned tables in this milestone.

## API Changes
### `POST /api/v1/auth/register`
Request:
```json
{
  "email": "engineer@example.com",
  "password": "strong-password",
  "display_name": "Engineer"
}
```

Response:
```json
{
  "id": "...",
  "email": "engineer@example.com",
  "display_name": "Engineer"
}
```

### `POST /api/v1/auth/login`
Request:
```json
{
  "email": "engineer@example.com",
  "password": "strong-password"
}
```

Response:
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

### `GET /api/v1/workspaces`
Protected. Returns workspaces where the current user is a member.

### `POST /api/v1/workspaces`
Protected. Creates a workspace and owner membership.

### `GET /api/v1/workspaces/{workspace_id}`
Protected. Requires membership in that workspace.

## Test Plan
Unit tests:
- password hashing verifies correct password and rejects wrong password.
- JWT creation/verification returns the expected subject and rejects invalid tokens.
- email normalization prevents duplicate mixed-case accounts.

API/integration tests:
- user can register.
- duplicate email is rejected.
- user can login and receive bearer token.
- protected workspace routes reject missing token.
- user can create a workspace.
- creator can list and read their workspace.
- second user cannot read first user's workspace.
- malformed workspace ID returns a controlled error.

Migration/runtime checks:
- Alembic migration applies to the local database.
- Docker Compose still starts.
- `GET /health` remains public and fast.

Validation commands:
```bash
make backend-lint
make backend-test
docker compose up --build -d
curl http://127.0.0.1:8000/health
docker compose down
```

## Acceptance Criteria
- Users can register and login.
- Passwords are stored only as hashes.
- JWT-protected routes reject unauthenticated requests.
- Users can create workspaces.
- Users can list only their workspaces.
- Users cannot access another user's workspace.
- Reusable auth and workspace dependencies exist for future milestones.
- Tests cover positive and permission-denied paths.
- Alembic migration exists and matches the SQLAlchemy models.
- No AI, RAG, LangGraph, dataset, or document behavior is implemented early.

## Risks
- Security risk: accidentally returning another workspace's existence or data.
- Test risk: only testing happy paths and missing cross-user denial.
- Architecture risk: putting permission checks inside route bodies instead of reusable dependencies.
- Scope risk: adding roles, audit logs, frontend login, or product tables too early.
- Dependency risk: password/JWT libraries can introduce noisy compatibility issues; keep choices conservative and tested.
- Migration risk: app models and Alembic migration can drift if generated carelessly.

## Human Review Checklist
- Confirm auth routes are under `/api/v1`.
- Confirm `/health` remains public.
- Confirm password hashes are never returned by API schemas.
- Confirm workspace membership is enforced by a reusable dependency.
- Confirm tests include user A denied from user B's workspace.
- Confirm no unrelated product modules or AI abstractions were added.
- Confirm migration and model definitions agree.
- Confirm error responses are explicit enough for debugging without leaking sensitive data.

## Operating Notes
After implementation:
- Create `docs/learning/milestone-2-auth-workspace-isolation.md`.
- Self-review for P0/P1/P2 security and architecture issues before moving to Milestone 3.
- Be able to explain in interviews why workspace isolation is the foundation for safe RAG, evaluation, and cost dashboards.
