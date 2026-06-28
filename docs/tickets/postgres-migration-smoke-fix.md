# PostgreSQL Migration Smoke Fix

## Goal
Fix a local deployment migration failure caught by browser smoke testing.

## Context
The Playwright smoke test failed before loading the UI because the live PostgreSQL volume had not applied recent migrations. Running `uv run alembic upgrade head` then exposed a migration-chain bug: Alembic's default `alembic_version.version_num` column is `VARCHAR(32)`, but revision id `0017_ai_run_model_config_attribution` exceeded that length. PostgreSQL rejected the version update, leaving the database at revision `0016_prompt_model_archive`.

## Requirements
- Keep the migration chain valid for PostgreSQL.
- Do not manually patch only the local database.
- Preserve the schema changes in the affected migration.
- Rerun migrations and browser smoke tests.

## Implementation
- Shortened revision id `0017_ai_run_model_config_attribution` to `0017_airun_model_cfg`.
- Updated `0018_workspace_role_presets` to point at the shortened `down_revision`.
- Left the filename and migration operations unchanged so the intent remains readable.

## Verification
- `cd backend && uv run alembic upgrade head` passed.
- `cd backend && uv run alembic current` reported `0022_agent_config_folders (head)`.
- `make frontend-e2e-docker` passed after applying migrations.

## Risk
This is safe for the current PostgreSQL volume because the failed migration left `alembic_version` at `0016_prompt_model_archive`. If another developer had already applied this migration in a non-PostgreSQL database using the long revision id, they would need to stamp or migrate that dev database manually.
