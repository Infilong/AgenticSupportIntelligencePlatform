# Browser navigation delay
## Goal
Diagnose and repair recurring initial-navigation delay without weakening browser acceptance.
## Context
The recovery UI passes focused tests, but full 10-worker runs time out in the existing editor
journey after spending about 59 seconds in page.goto. The final interaction location changes.
## Requirements
Preserve traces and content-free timings. Distinguish Chromium connection setup from server work.
Keep assertions, overall timeouts and concurrency unchanged unless evidence justifies a design change.
## Non-goals
Unproven DNS/proxy flags, global workstation configuration changes or hiding failed tests.
## Acceptance Criteria
Identify a reproducible cause, verify a targeted correction and pass the complete browser suite.
## Plan
1. Inspect slow navigation timing and compare a controlled loopback experiment.
2. Reproduce actual multi-worker browser startup/setup conditions with a bounded diagnostic.
3. Apply only evidence-supported correction and rerun acceptance.
## Verification
Full Chromium suite with 10 workers and 75-second test timeout. Preserve .artifacts logs/traces.
## Risks
HAR derived DNS/SSL values can mislead; use raw CDP timing. A passing unrelated probe does not
prove that full-suite startup conditions are fixed. Do not retry the suite blindly.
## Progress
2026-09-08 separate-worker follow-up: bounded standalone probes launched ten separate browsers
per condition, first immediate navigation and then navigation after twenty health requests and
a five-second delay. All 20 passed in 611-1479ms; DNS phases stayed below 774ms.
Evidence: `.artifacts/loopback-worker-probe.cjs`, `.json` and `.log`. This excludes neither the
actual application setup workload nor Playwright tracing overhead.

The actual editor journey repeated ten times with ten workers failed 10/10 at the unchanged
75-second timeout (`.artifacts/navigation-editor-repeat.log` and trace directory). This did
not reproduce the original long DNS phase: all ten document response DNS phases were below
11ms. Several save-button clicks took 32-54 seconds; other copies accumulated slow setup and
interactions. In the first trace the button was visible/enabled/stable within 0.3 seconds;
almost 38 seconds elapsed between performing the click and click completion, before the
scheduled-navigation wait. Do not label this an element locator or navigation-wait defect.
Timing extraction: `.artifacts/navigation-editor-repeat-summary.json`.

Both diagnostic processes are terminal. No application or test settings changed. Next isolate
the save action's browser main-thread/trace overhead with a bounded profile; distinguish this
ten-heavy-journey load failure from the original mixed-suite DNS stall. A standalone health
probe is not equivalent to ten full authenticated application journeys. Keep the original
mixed-suite failure open and do not ship resolver flags or increase timeouts from these results.

2026-09-08: full runs pass 26/29, then 28/29 twice after fixing a new ambiguous status locator.
Latest: `.artifacts/embedding-recovery-ui-diagnostics.log`. Editor navigation raw CDP timing
shows dnsStart 0.302ms, dnsEnd 55837.524ms, connectEnd 55838.886ms and headers 55844.465ms;
proxy/SSL phases are absent. Navigation diagnostics are attached by agent-network-fixture.ts.
A shared-browser probe with ten contexts per condition passed 20/20 at <=1012ms, both default
and explicit loopback mapping (`.artifacts/loopback-dns-probe.json`). No flag was shipped.
Next reproduce per-worker browser startup and pre-navigation API setup; the shared-browser
probe does not reproduce the full suite's separate worker browsers and workload.
## Decisions
Keep precise notice selectors for overlapping success/loading statuses; retain all other assertions.
## Findings
The editor timeout occurs after a long initial navigation, not proof of broken input editing.
## Final Result
Open. Recovery UI passes focused acceptance; full regression is not green.
