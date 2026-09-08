# Backend guide

Start with the [current code map](../docs/code-map.md) and [project context](../docs/PROJECT_CONTEXT.md).

## Ownership

| Directory | Responsibility |
| --- | --- |
| `app/main.py` | App assembly and middleware |
| `app/cli/` | Standard-library HTTP client, commands and protected local sessions |
| `app/api/` | HTTP contracts, dependencies and error translation |
| `app/dependencies/` | Current-user and workspace permission checks |
| `app/schemas/` | Pydantic request/response boundaries |
| `app/services/` | Business behavior, provider adapters and current persistence orchestration |
| `app/models/` | SQLAlchemy entities and relationships |
| `app/db/` | Metadata, engine and request session lifecycle |
| `app/core/` | Settings, token security and language primitives |
| `alembic/` | Versioned schema changes |
| `tests/` | Domain/API regression tests with mock providers |

Read the [API guide](app/api/README.md), [service guide](app/services/README.md) or
[migration guide](alembic/README.md) only when that boundary changes.
The [CLI guide](../docs/cli.md) covers installation, commands, credentials and exit codes.

## Working rules

- Routers validate and translate errors; services own business decisions. Keep database queries
  outside routers when changing the relevant path, without unrelated bulk refactors.
- Every workspace operation validates membership/permission at the HTTP boundary and keeps
  workspace predicates in service queries, including joins and child-resource lookups.
- Make multi-write transaction ownership explicit. Existing service-level commits mean callers
  cannot assume that one request is atomic.
- Record AI usage and workflow evidence; automated tests must never depend on real API keys.
- Keep new files under 300 lines and shrink existing oversized files as responsibilities move.

## Running and testing

From the repository root, `docker compose -p asi-verification up -d --build` starts a separate
verification volume. The API image applies migrations before serving on port 8000.
Do not reuse a Linux `.venv` from Windows or vice versa; use containers or a fresh native env.

Native backend commands: `uv sync --frozen --extra dev`, `uv run pytest -q`,
`uv run ruff check .`, `uv run alembic upgrade head` (from this directory).
See [testing](../docs/testing.md) for container commands and their coverage limits.

## Known production gaps

Request middleware now emits request IDs and structured HTTP outcome logs; see
[observability](../docs/observability-design.md) for its privacy and correlation limits.
Staging/production now reject the public default JWT signing key and keys shorter than 32 bytes.
Allowed environments are local, development, test, staging and production; typos fail startup.
Supply a cryptographically random `JWT_SECRET_KEY` through deployment secrets. Length validation
does not prove entropy, rotation or safe storage. Configuration error text suppresses input values.
The development Compose file fixes `ENVIRONMENT=local`; a real deployment must explicitly change
that setting and inject its signing key. The example `.env` alone does not convert Compose to production.

Agent model dispatch now uses budget reservations; review transitions use row locking and an
atomic state/audit commit. See [service ownership](app/services/README.md) for these boundaries
and [testing](../docs/testing.md) for PostgreSQL evidence. Direct/vector-RAG baseline generation
now shares reservation admission; exact billing, durable recovery and deployment remain gaps in the
[quality score](../docs/QUALITY_SCORE.md). An API health response alone does not prove them.
