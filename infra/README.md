# Runtime and infrastructure guide

[docker-compose.yml](../docker-compose.yml) starts API, task worker, frontend, PostgreSQL/pgvector and Redis.
The worker runs `python -m app.worker` after API health succeeds, so migrations precede polling.
Both processes use the same database and provider environment. New Work requests need the worker;
if it is unavailable they remain queued and can still be stopped. Inspect `docker compose logs worker`.
[Backend Dockerfile](../backend/Dockerfile) applies Alembic then starts Uvicorn.
[Frontend Dockerfile](../frontend/Dockerfile) currently starts the Vite development server.
[Postgres initialization](postgres/init/001_enable_pgvector.sql) enables the extension.

## Built web/API image

Build from the repository root with
`docker build -f infra/Dockerfile.web -t asi-web .`. This optional image compiles the frontend
with an empty `VITE_API_BASE_URL`, serves it at the API origin, and runs as UID 10001.
Node/npm exist only in the build stage. The default Compose profile remains a development setup.

The image defaults to `ENVIRONMENT=production` and requires an externally supplied non-default
`JWT_SECRET_KEY`. Supply `DATABASE_URL`, `REDIS_URL` and provider settings explicitly in a
private runtime env file or secret injection mechanism. An operator-managed private network
must connect the API to its database/cache; do not reuse verification credentials for deployment.
Use `EMBEDDING_PROVIDER=mock` with no provider key only for explicitly labeled simulation.
Do not place secrets in frontend build variables: they are public browser assets.

Run migrations as a separate controlled operation before starting the application. For example,
with an existing `support-private` network and a protected `/secure/asi.env` supplied by the
operator (substitute the actual paths/network):

```sh
docker run --rm --network support-private --env-file /secure/asi.env asi-web alembic upgrade head
docker run -d --name asi-web --network support-private --env-file /secure/asi.env -p 127.0.0.1:8080:8000 asi-web
docker run -d --name asi-worker --network support-private --env-file /secure/asi.env asi-web python -m app.worker
```

Verify `/health`, migration head, `/` and the complete browser journey before admitting traffic.
The worker is required for queued tasks. Run it from the same image and with the same database
and provider configuration as the API; supervise both processes. The compiled verification
runner starts a worker and checks it remains running throughout the browser suite.
The image does not migrate on every server start. Back up and review migrations before applying
them to existing production data; migration rollback and release rollback are separate decisions.
Terminate TLS at an explicitly configured trusted ingress in front of the loopback endpoint.
Process supervision, secret rotation, monitoring, retention, load/recovery targets and hosted CI
remain deployment work; this image alone is not a production certification.

`FRONTEND_DIST_PATH` defaults to `/app/web` in this image. Other API launches omit static
serving unless this setting points to a build containing `index.html` and `assets/`; incomplete
builds fail startup. Only `/` and `/assets` are served. The index is not cached; assets support
conditional requests. Unknown API/page paths remain 404, and API authentication is unchanged.
The root `.dockerignore` excludes local env files, Git state, artifacts and installed dependencies
from this build context. Keep backend dependency/runtime changes synchronized between this
Dockerfile and the development backend Dockerfile. [Verification](../docs/testing.md#built-web-runtime).

## Local operation

- Use `docker compose -p asi-verification up -d --build` for verification data isolation.
- Check `ps`, API logs, `/health`, frontend HTTP response and `alembic current` before testing.
- Preserve container/volume names in evidence. Inspect live state before restarting.
- `docker compose -p asi-verification stop` stops this stack without deleting its data.
- Never use `down -v` against user data as a routine repair action.

## Production boundary

This Compose file is a local profile. API/frontend/PostgreSQL/Redis host ports bind explicitly
to 127.0.0.1, so the default profile is intended for access from this computer. Containers still
use service names on the Compose network; local database tools keep localhost access. The
FRONTEND_PORT override changes the port, not the loopback interface. Remote team access needs
an explicitly designed deployment profile with TLS and access controls; do not casually change
these bindings to wildcard addresses. Loopback binding does not protect against other local
processes or containers with network access. The profile uses development database credentials
and does not override the default JWT signing secret. Do not present it as a
hardened deployment. Redis presence does not imply implemented background jobs.

Before release: require non-default secrets, private database/cache networking, built frontend
assets, non-root processes, controlled migration execution, readiness checks, graceful shutdown,
log retention, monitoring and alerts, demonstrated restore and rollback procedures.
Set explicit workload, latency, availability, RPO/RTO and spending targets; record measured results.

See [testing](../docs/testing.md), [scale path](../docs/scale-path.md), and the
[production audit](../docs/audits/production-readiness-2026-09-07.md).

## Local logical backup/restore drill
With Docker Desktop and the populated synthetic `asi-verification` stack running, first run
`multilingual-workflow.spec.ts` to create the known EN/JA/ZH journey fixtures, then stop test
writers and run `python scripts/verify_database_restore.py` from the repository root. The script
is deliberately fixed to that project/service and development database; it is not a production
backup command. It saves a binary custom-format pg_dump under `.artifacts/database-restore-*/`,
restores into a uniquely created database, compares all public-table row counts and ordered
JSON content hashes, and checks the restored Alembic revision. It uses pg_dump/pg_restore from
the PostgreSQL container, including extension/schema/index/constraint restoration. Cleanup drops
only the newly created database, never the source. Before cleanup, a separate API container
uses the restored database with mock embeddings and no provider key. The probe logs in with
existing synthetic journey passwords, reads retained resources/traces/reviews/evaluations/costs,
checks anonymous/foreign-workspace denial and creates one cited durable task per language.
It replays each admission request to verify the same run is returned, executes through the task
worker, reads the run/history, and stops a second queued task before worker execution. The stopped
task must have no model calls or proposed actions. All probe writes stay in the disposable database.
`application.log` records API outcomes; source fingerprints must still match after the probe.
A report persists on success or failure;
inspect its target and cleanup fields if interrupted or cleanup fails before retrying.

Source manifests before/after the dump and after restore must match. Concurrent application
writes make this comparison fail; choose a quiet window rather than hiding that failure.
The dump uses PostgreSQL's consistent snapshot, but this drill does not coordinate snapshots
across other services. Full-table JSON sorting/hashing and reading the archive into memory are
appropriate only for this small synthetic dataset. Hashes detect accidental drift, not malicious
tampering. Dumps contain application content and password hashes: keep artifacts private and
ignored, and apply separate encryption/retention/access controls to any real backup process.

Passing proves local logical data restoration and scoped API operation on the restored data.
It does not prove browser/network cutover, external/offsite
backup, point-in-time recovery, automated scheduling, crash recovery, or measured RPO/RTO.
See [restore evidence](../docs/testing.md#local-database-restore) for the verified scope.
