# Milestone 2: Auth And Workspace Isolation

## What Was Built
Milestone 2 adds database-backed users, JWT login, workspace creation, workspace membership, and reusable FastAPI dependencies for current-user and workspace-member checks.

## Why Companies Care
AI systems often retrieve private documents and expose cost, evaluation, and trace data. Without workspace isolation, RAG and agent workflows can leak customer data across tenants. Employers care because this is a production safety boundary, not a cosmetic feature.

## How This Project Uses It
Every future workspace-owned API will depend on the same membership check introduced here. A user can list only their own workspaces, read only workspaces they belong to, and receives no access to another user's workspace.

## Design Tradeoffs
- JWT access tokens are stateless for local-first simplicity; refresh tokens and revocation are postponed.
- PBKDF2 password hashing uses Python stdlib to avoid early dependency complexity while still avoiding plaintext passwords.
- SQLite is used in tests for speed, while Alembic and Docker target PostgreSQL for local runtime.
- Non-member workspace detail returns 404 to avoid confirming whether another workspace exists.

## Failure Modes
- Route authors may forget to use `require_workspace_member` on future workspace routes.
- Tests can miss cross-user denial if they only check happy paths.
- JWT secrets must be replaced outside local development.
- Audit logging is not implemented yet, so auth events are not recorded in Milestone 2.

## Interview Explanation
I built auth before RAG because retrieval quality is not enough in a multi-tenant AI system. The platform needs a reliable tenant boundary so documents, graph traces, evaluations, and cost summaries cannot leak across workspaces. I made the permission check reusable so future features inherit the same access-control pattern.
