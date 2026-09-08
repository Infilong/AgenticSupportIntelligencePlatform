# Fresh rebuild instructions

## Current authority

- This is `codex/fresh-start`, a new root history. The previous app is archived.
- [REBUILD_PLAN.md](REBUILD_PLAN.md) owns V1 scope, roles, topology and release gates.
- M0 preparation is authorized. Do not automatically continue to M1 without a start instruction.
- Earlier implementation goals and old instruction files are historical, not active requirements.
- Only OpenAI-provided Codex tools and skills are permitted; no custom/third-party skill bundles.

## Read only relevant context

- Current state and next action: [docs/STATUS.md](docs/STATUS.md).
- Runtime/state ownership: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Pass/fail gates: [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md).
- Setup and recovery boundaries: [docs/RUNBOOK.md](docs/RUNBOOK.md).
- Fixture contract: [evals/README.md](evals/README.md).
- Do not treat planned behavior or generated documentation as implementation evidence.

## Working commands at M0

From the repository root, Python 3.12+ and Node.js 22+:

```text
python scripts/manage.py doctor
python scripts/manage.py doctor --offline
python scripts/manage.py verify-prep
python scripts/manage.py verify-browser
python scripts/manage.py evidence
```

- `doctor` reads tools, Docker availability, registry access and proposed port availability.
- Registry access, browser execution and Docker may need sandbox approval; report the actual result.
- `verify-prep` tests fixture integrity and preparation failure detection, not application behavior.
- `verify-browser` launches project-local Chromium with a synthetic environment probe only.
- See RUNBOOK for first-time browser installation; do not reuse archived node_modules.
- Application start/migrate/seed/live commands do not exist yet. Do not invent success output.

## Isolation and permissions

- New runtime namespace: `asi-rebuild-v1`, proposed loopback ports 5180/8010/5440.
- Preserve `asi-verification` and all existing database volumes, secrets and backups.
- Ignored old files are preserved in `.artifacts/legacy-local-m0-20260908/`.
- Do not reuse old `.env`, schemas, runtime instances or dependencies automatically.
- No Redis, cloud deployment, external vector service or general-purpose job platform.
- Local checkpoint commits are authorized; new pushes, merges and public deployment need approval.
- Routine dependencies within the approved stack are allowed for the authorized milestone.
- Live API spending defaults to zero. A key is not spending authorization. Never print secrets.

## Implementation boundaries

- Keep one focused implementation owner; use bounded read-only review only when beneficial.
- UI renders server decisions. Backend owns auth, workspace scoping, transactions and accounting.
- Workspace data must be scoped before retrieval, tools, source previews and model context.
- Queue payloads, documents and customer messages cannot grant authority.
- PostgreSQL owns business data/jobs. LangGraph checkpoints own workflow continuation.
- Repeated delivery/resume must not duplicate published results or human decisions.
- Preserve original inputs, historical evidence and uncertainties in model-call accounting.
- Prefer maintained provider SDKs and graph persistence; do not build custom HTTP clients.
- Keep files cohesive, normally under 300 lines. Split by responsibility, not arbitrary length.
- Do not create empty architecture folders or duplicate implementations.

## Verification and checkpoints

- Start each slice from an acceptance ID or reproduced defect.
- Check current git state, relevant files and live process handles before acting.
- Run focused checks, then the affected real application journey when implemented.
- Offline application E2E uses the actual UI/API/database/worker; fake only external AI providers.
- Database/vector/isolation tests require PostgreSQL; SQLite does not prove these boundaries.
- Separate fixture consistency, software correctness, browser behavior and live AI quality.
- Never weaken tests or silently change release criteria to fit the implementation.
- Retain failed evidence and explain repairs. A retry does not erase a failure.
- Record commit/source fingerprint, commands, results and evidence locations at checkpoints.
- Keep STATUS concise and current; relevant changes make prior evidence stale.
- Do not commit `.artifacts`, real customer data, credentials or generated dependencies.

## Bounded autonomy

- Resolve routine choices within the authorized scope; no repeated minor permission requests.
- Ask for missing access/spend authority or material product/security changes.
- Target 30–60-minute slices; reassess by 90 minutes and diagnose after three failed repairs.
- Stop unattended work after four hours with saved state and exact resume instructions.
- Do not spawn new work to prolong a completed scope. M0 ends with its verification checkpoint.
- Report verified, failed, skipped and not-verified results separately.
- Only the full release acceptance matrix can support a release-completion claim.
