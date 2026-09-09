# Packaged release smoke in CI

## Execution brief

User outcome: prevent packaged-app regressions as the goal advances; BOOT/AUTH/TENANT/UX.
Normal CI verification slice, root implementation owner. Follow root, infra, scripts, frontend
and docs guides. Existing authorized branch pushes only; no deployment or model spending.

Observed gap: Verify runs the development-server journey, while built-release evidence is local
only. Reuse the existing three-case release.spec.ts against a fresh isolated Ubuntu CI stack.
Keep a separate bounded job, existing pinned setup actions, disposable seeded identities and
failure diagnostics plus an unconditional cleanup step. Preserve volumes; never touch development
or archive stacks. Do not add product behavior, providers, inference downloads or new tools.

Verify YAML structure, existing local release smoke, independent workflow/scope review,
freshness/preparation, then push the coherent checkpoint and inspect the actual CI result.
Repair observed workflow failures without lowering assertions. Report this as a no-API packaged
smoke, not real-model capacity or full release readiness. Continue within the14:58 UTC boundary.

## Evidence

Local baseline: three release journeys pass in8.4s at
`.artifacts/m6/release-ci-baseline-20260909`. One launch never started after approval review timed
out; the instructed single retry launched successfully. No application failure was retried away.
Starts from pushed five-session checkpoint48f9409. Hosted execution remains pending until push.
Workflow YAML parses with the existing backend environment. A first uv-based parser invocation
could not read its global cache under the sandbox; direct execution of the installed environment
passed. Independent workflow review found no actionable defect. Cleanup can be interrupted by
job timeout/runner loss; browser files are not currently uploaded from the ephemeral runner.
Independent documentation review corrected cleanup certainty and renewed the three affected
receipts. Freshness check passes;46 preparation checks pass in10.699s at
`.artifacts/m0/prep-20260909T131254447483Z`. This evidence note follows that run without changing
workflow or owning documentation. Before push, hosted verification was the remaining completion step.

Hosted result confirmed at13:18 UTC: pushed revisionf1a64dc5388e8e7b82111f2d400b9e0002dc81e0,
GitHub Verify34355803730 completed successfully, including the packaged release job. A later
job-step inspection confirmed build/migration, seed, protected browser journey and cleanup all
executed successfully; failure diagnostics skipped as intended. All five workflow jobs passed.
This plan is closed. Native zoom stopped separately at the Computer Use observation boundary;
no hosted failure or product repair remains for this CI slice.
