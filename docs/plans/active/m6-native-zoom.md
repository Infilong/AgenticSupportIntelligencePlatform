# Native Chrome zoom verification

## Execution brief

Close a specific UX evidence gap: browser-native200% zoom, beyond earlier responsive/CSS-size
checks. Normal bounded QA slice, root owner; follow frontend/docs guides and OpenAI Computer Use
skill. Open a separate installed-Chrome test window with isolated seeded release credentials.
Use native browser controls through Computer Use; never change user Chrome's profile or pretend
CSS/device/pinch scaling is browser zoom. Verify actual native zoom UI plus baseline-to-zoom
device-pixel ratio and viewport change. Inspect main admin screens, new-message/clarification/
workflow flow, keyboard focus, overflow and screenshots. No generation or RAG tuning.

Add an opt-in reproducible Playwright journey that waits for an attended native zoom change;
standard unattended CI must skip it. Preserve records/screenshots and any failure. Fix only
demonstrated UI problems. Independently review claims, update owning docs and checkpoint.
At this slice's start, the release CI job was reviewed/pushed asf1a64dc with hosted execution
pending. It subsequently passed34355803730; see the [completed CI record](../completed/m6-release-ci.md).
Continue only within the existing14:58 UTC boundary.

## Evidence

Pending. Loading repository Playwright inside node_repl failed twice with an ESM/CJS export
error before any browser launched. Use the normal repository Playwright runner (already proven
for other journeys), reserving Computer Use for Chrome's native controls.

At13:18 UTC, Computer Use stopped for this turn because it could not determine the current
browser URL on Windows confidently enough to enforce policy. No desktop inputs were issued;
native zoom was not changed or verified. The isolated Playwright runner was interrupted after
this stop (exit1); this is interrupted verification, not a demonstrated application defect.
The opt-in harness is preserved at
`.artifacts/m6/native-zoom-20260909/parked-native-zoom.spec.ts`, outside the passing test suite,
and is not independently reviewed. Do not count it as UX
evidence or bypass the tool restriction. Existing user Chrome was not used for test login.
Resume by reviewing this harness and restoring an approved native-browser observation path;
other completed local/hosted checks remain as recorded. No full-goal completion claim.
