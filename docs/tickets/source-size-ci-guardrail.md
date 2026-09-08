# Source size CI guardrail

## Goal and context
Turn the existing approximately 300-line rule into an executable CI check.
The production-readiness review found large application files continuing to grow.

## Requirements and design
- Count physical lines, including blank lines, consistently on Windows and Linux.
- Check Python and TypeScript (`.py`, `.ts`, `.tsx`) under `backend/app` and `frontend/src`.
- Reject new files above 300 lines and growth beyond an existing file's baseline.
- Require lower baseline values after shrinking oversized files; remove resolved or deleted entries.
- Fail explicitly if source roots or baseline configuration cannot be read.
- Use Python's standard library so this gate runs without application dependencies.

## Files and responsibilities
- `scripts/check_source_sizes.py`: source discovery, validation and CLI diagnostics.
- `scripts/source-size-baseline.json`: current oversized-file debt, not a target architecture.
- `scripts/tests/test_source_sizes.py`: boundary, regression and configuration failure tests.
- `.github/workflows/ci.yml`: independent source-size job.
- This ticket: operating instructions, scope and acceptance evidence.

## Non-goals, database and API changes
No application refactor, dependency, database migration, API, permission, UI or model-call change.
CSS, generated assets and test-file sizes are outside this first gate's scope.
File length does not prove separation of concerns; dependency-boundary checks remain future work.

## Test plan and acceptance criteria
Run `python -m unittest discover -s scripts/tests -v` and `python scripts/check_source_sizes.py`.
The current checkout must pass; a 301-line new file or one-line legacy growth must fail.
Missing/invalid baselines must fail rather than silently exempting files.

## Risks and human review
Review baseline additions/increases as architecture exceptions, never as a routine way to pass CI.
The baseline is versioned code: this gate does not prevent a PR author from editing its limits.
Configure the `source-size` job as a required branch check before relying on it as a merge gate.
Do not compress code or remove useful comments to satisfy line counts; split responsibilities.

## Operating notes
Run both commands from any clean checkout with Python 3.12. The checker also works from another
working directory; `--root PATH` is available for fixture testing.
After a split, manually lower or remove the affected baseline entries and rerun the checker.
Existing oversized files are admitted at their initial size to support incremental recovery.

## Validation result (2026-09-07)
All 9 standard-library tests passed on Python 3.12.8. The source check passed for 124 files,
with 24 existing oversized files baselined. `git diff --check` passed.
Hosted CI and branch protection were not changed remotely or verified. Application suites were
not rerun for this tooling-only ticket; their earlier environment blockers remain unresolved.
