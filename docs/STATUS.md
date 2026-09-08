# Current status

Milestone: **M0 preparation complete**. Product implementation is not authorized by this task.
Branch: `codex/fresh-start`. Starting revision: `c70f254562463b8cf8bc342e30d66f57e6058eb5`.
The M0 checkpoint is the local commit titled `chore: prepare isolated V1 rebuild (M0)`;
resolve its exact hash with `git log -1 --format=%H` after the checkpoint is created.
The previous implementation goal is retired; do not resume it.

## Preparation evidence

- Doctor passed Python, Git, uv, Node/npm, Docker/Compose, registries and new-port checks.
- Fresh pinned Playwright/Chromium passed multilingual rendering and keyboard interaction.
- Fifteen fixed cases reference versioned synthetic documents; two cases require English
  evidence for Japanese/Chinese questions. Obsolete policy remains explicitly inactive.
- Preparation tests cover fixture integrity, missing/inactive references, tool/port failure,
  failed-command evidence, source-change detection and documentation links.
- Final verification: 10 preparation tests passed; one Chromium environment test passed.
  All five PREP gates are satisfied for this local Windows preparation scope. Product gates
  remain NOT_IMPLEMENTED, and Linux/macOS preparation has not been verified.
- Final command results and exact code fingerprint: `.artifacts/m0/summary.json`.
- Browser trace/screenshot and command evidence: timestamped directories under `.artifacts/m0/`.

M0 verification is preparation only. All product gates in [ACCEPTANCE.md](ACCEPTANCE.md) are
NOT_IMPLEMENTED. Live provider quality is NOT_VERIFIED; application API spend is $0.
The full policy corpus, 30+ cases, numeric quality thresholds and load targets remain to prepare
before M2 tuning. No claim is made about production readiness or app usability.

## Failures and repairs

- Old frontend directory rename was blocked by a Windows handle; moving its contents preserved
  old dependencies without reusing them. No old service was restarted or volume changed.
- npm metadata failed under sandbox network restrictions; an approved retry succeeded.
- Doctor's offline result is PARTIAL so skipped network checks cannot masquerade as full readiness.
- Final browser capture exposed Windows GBK decoding of UTF-8 output. The evidence wrapper now
  preserves raw bytes, renders UTF-8 safely and has a regression test. The failed run's browser
  output directory is retained; it was not treated as an application/browser acceptance pass.

## Next exact action

Stop after the M0 checkpoint and user review. On explicit M1 authorization, begin with an
isolated runnable foundation: implement Compose/app/worker/database configuration, compatible
locked dependencies, an initial schema and health/readiness. Then deliver browser login and
workspace access denial as one connected feature. Do not create the entire target topology
up front. Add commands as they become executable and update this file at meaningful checkpoints.

No unresolved access blocker prevents M1 offline development. Live-provider credentials and
an explicit spending cap are needed before M2 live verification; do not ask repeatedly or
treat their absence as authorization to replace live acceptance with mock results.
