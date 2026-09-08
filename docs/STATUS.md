# Current status

Goal: **M1–M6 authorized and active**. Current milestone: M1 foundation.
Branch: `codex/fresh-start`. Goal starting revision: `2c292d08b5ff9d577276c8513fc53582a1ba93d4`.
[Active execution plan](plans/active/m1-foundation.md) owns slices, decisions and exact next steps.
Normal verified commits/pushes to this branch are authorized. No merge/deploy/paid API authority.

## Current work

First M1 slice: automated coverage of local guide links and instruction limits, plus
Linux/Windows preparation CI. All 13 local regression tests passed; remote CI inspection is pending.
Next: isolated runnable API/PostgreSQL foundation, then auth/workspaces and real browser UI.
Continue through the full goal within authority; no milestone-by-milestone approval is needed.

## Verified baseline and remaining gaps

- M0 checkpoint: `d3c8e4b1317507f8f0fd5e47d386cdfcb7d1e41c`; 10 preparation tests and one
  synthetic Chromium environment probe passed at that source snapshot. This was not app QA.
- The previous implementation is archived and must remain untouched. Runtime observations
  from M0 require reinspection before operations; no existing process is assumed live.
- Fifteen synthetic EN/JA/ZH cases exist. Full corpus, quality thresholds, live retrieval,
  actual UI/API/worker flows, restoration and release gates remain incomplete.
- [Preparation review](PREPARATION_REVIEW.md) records earlier findings; this slice addresses
  automated guide coverage and initial CI. Runtime and architecture enforcement remain open.
- Evidence is timestamped under `.artifacts/m0/` for preparation checks; summaries are mutable
  and whole-repository changes invalidate earlier source fingerprints.

## Access and failures

User currently has no API. Codex cannot act as the app's runtime API. No paid calls authorized;
use explicit deterministic test providers while implementing real integration interfaces.
User requests a Codex-assisted development handoff: app requests can be answered by this session
and imported through the provider contract, with accurate provenance and separate verification.
Live API/embedding quality remains NOT_VERIFIED and cannot be passed from mocks or handoffs.
M0 failures and repairs (Windows file handles, sandbox network access, UTF-8 capture) remain
recorded in the preparation checkpoint/runbook; preserve failed evidence.
