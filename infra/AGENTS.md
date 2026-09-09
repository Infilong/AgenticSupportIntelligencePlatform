# Infrastructure guidance

Scope: this directory; also read this guide for root runtime/configuration changes.
Read the [root director](../AGENTS.md) and [status](../docs/STATUS.md) for current progress.

- [Architecture](../docs/ARCHITECTURE.md) owns runtime decisions;
  [runbook](../docs/RUNBOOK.md) owns namespace, ports, setup and recovery instructions.
- Use the isolated rebuild namespace and volumes. Preserve the archived stack, backups,
  database volumes and secrets. Never treat old data as disposable test data.
- Do not automatically reuse archived environments, dependencies or schemas.
- Keep the approved local app/worker/PostgreSQL design; no Redis, cloud deployment,
  external vector service or general-purpose job platform in V1.
- Keep secrets out of images, Git and logs. Live spending defaults to zero.
- Pin compatible dependencies and document configuration defaults and runtime ownership.
- Validate resolved targets before destructive filesystem operations and recheck process
  identity before restarting. New deployment or destructive data work requires authority.
- Verify startup, health, migrations and restoration against an isolated environment when
  implemented. Configuration files alone do not prove those flows work.
- Follow [scripts guidance](../scripts/AGENTS.md) for command implementations and evidence.
