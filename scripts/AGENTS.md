# Developer tooling guidance

Scope: this directory and its descendants. Read the [root director](../AGENTS.md).

- [Runbook](../docs/RUNBOOK.md) owns executable commands and installation recipes.
  Keep `manage.py` a small dispatcher; separate environment probes, evidence and fixture checks.
- Commands must preserve exit codes, use bounded timeouts and explain skipped checks.
  Do not print secrets or capture environment-variable values in reports.
- Keep doctor read-only. Revalidate live process handles before any authorized restart.
- Retain timestamped command logs and source fingerprints under ignored `.artifacts`.
  Changed source invalidates earlier evidence; environment observations can expire independently.
- Preserve raw process output and handle UTF-8 on Windows. Never hide a failure behind retries.
- Use [infrastructure guidance](../infra/AGENTS.md) for runtime-changing commands, even
  when their implementation lives here. Validate resolved paths before filesystem operations.

## Verification

- From the repository root, run `python scripts/manage.py verify-prep` for preparation
  tooling and fixture checks. Keep failure-path tests meaningful; do not mirror implementation.
- For browser harness changes, also run `python scripts/manage.py verify-browser`.
- `python scripts/manage.py evidence` reports current versus stale evidence; neither an
  environment probe nor fixture integrity test proves product functionality.
- Register new commands only when executable and update the runbook in the same change.
- Run `python scripts/docs_freshness.py check` before checkpointing; follow the
  [freshness protocol](../docs/DOC_FRESHNESS.md) for stale references or review receipts.
