# Minimal settings and usage

Outcome: M4/TRACE/UX — admins can choose the default language for new manual messages, inspect
actual provider configuration, and members can inspect workspace-scoped recorded model activity.
Normal scoped implementation, root sole owner. Read root/backend/frontend/docs guides.
No provider integration, paid calls, new RAG strategies, evaluation dashboard or infrastructure.

Add one workspace language field with an additive migration; explicit message language continues
to control processing and imports. Settings shows actual local embedding/reranking identities
and attributed development generation; configuration is not a live-provider readiness test.
Quality starts with usage: bounded1–90-day SQL aggregation, counts by status, known tokens/cost
and missing-measurement counts, per-model groups. Never turn unknown charges into verified zero,
sum durations into wall time, or handoff waiting into generation inference. No raw customer data.
All writes admin-only; reads scoped membership; provider details contain no secrets/paths.

Verify PostgreSQL aggregate accuracy/time bounds/foreign denial/admin-only changes; frontend
build/tests, browser Settings→save→new message default, Quality known/unknown metrics at
360/768/1440 and viewer settings denial. Independent backend/UI/docs review, focused regressions
and branch checkpoint. Full goal and external generation remain incomplete.

Preceding import checkpoint a095a08 pushed;45 prep checks passed at
`.artifacts/m0/prep-20260909T093003893465Z`. Full141PGpass remains preceding-boundary evidence.


18 PostgreSQL checks pass, including actual1/7/90-day inclusion and22-group truncation;33 frontend
checks and build pass. Initial build exposed six old workspace fixtures missing the newly
generated default_language field; fixtures now match the public contract. Independent review
found no backend defect and requested the time-window checks, now passing. UI review found a
browser wait that mistook pending-button disablement for commit; it now waits for PUT success
and refreshed data before reload/restoring defaults. No assertion was weakened.

Seven real browser journeys pass in25.5s at `.artifacts/m4/settings-usage-browser-20260909`; screenshots inspected. All four services healthy; no outstanding review blocker.
