# Current status

## Authority and next action

Current slice: [automatic answers and intervention routing](plans/active/demo-outcome-routing.md).
The user now requires supported automatic answers, exception review, missing-support intervention
and retained set-aside messages, then completion of M5/M6. This supersedes the earlier demo-only
pause and blanket admin-review requirement. Actual local runtime evidence at
`.artifacts/demo-routing/final/case-01..10.json` records four automatic answers, two policy
reviews and four missing-support interventions. Weather/photosynthesis conservatively went to
human intervention, not set-aside; this classifier limitation remains. Six separate EN/JA/ZH
meaningless/spam cases are retained as completed/set_aside (`noise-01..06.json` in the parent
directory). Initial ValidationError attempts remain preserved; reason-only abstentions now use
their nonempty reason while retaining structured model output and dropping unrelated citations.
Sixteen PostgreSQL checks passed55.29s before that provider normalization at
`.artifacts/m0/demo-routing-api-20260910T044506954108Z`; final16 provider units passed1.38s and
Ruff/182-file formatting pass. Final frontend build and48 tests pass9.79s. Chrome inspected an automatic answer/exact source
and missing-support controls without approve/edit. First screenshot capture timed out; later
chrome-missing.png and chrome-set-aside.png under `.artifacts/demo-routing/` were captured and
visually inspected by the coordinator, with no review controls on the set-aside outcome.
Next: connect separately versioned local generation to the frozen four-pipeline M5 comparison,
preserving direct/no-retrieval behavior, comparable settings and full original denominators.
This smoke is not full semantic evaluation, complete regression or M5/M6 completion.

Earlier local-generation evidence remains valid for its historical draft-only behavior: six
EN/JA/ZH questions reached cited drafts with Qwen7B; see the
[local-generation record](plans/active/demo-local-generation.md). M1–M6 remain authorized and
incomplete. Finish the agreed acceptance work after routing verification; avoid speculative
features and deferred RAG tuning. The user removed the execution time limit on2026-09-10.
There is no fixed unattended deadline; continue the authorized goal until verified completion,
a genuine blocker or a new user instruction. Earlier execution windows are historical.
Preserve the archive, all existing databases, unrelated edits and secrets. Small verified commits
and pushes to `codex/fresh-start` are authorized; merging, public deployment and paid calls are not.

The [status-navigation checkpoint](plans/completed/m6-status-navigation.md) preserves prior evidence.
The remaining M5 boundary is assessed in [generation pipelines](plans/active/m5-generation-pipelines.md).
The [packaged admin journeys](plans/completed/m6-release-admin-journeys.md) are reviewed and pushed.
Current: four-pipeline checkpoint81e68b0 is committed/pushed. Its real CLI/browser demo and
cold-worker first-attempt preparation pass;17 focused database tests,77 units and56 prep checks
pass. Full local regression timed out420s after126 displayed passes; hosted CI34380249837
passed all five jobs, including real PostgreSQL regression. Frozen-run controls are repaired;
2 focused database and2 component checks, frontend build and real frozen/ordinary browser views
pass. Frozen controls checkpoint4002e78 is pushed and hosted CI34381303388 passed.
The comparison administration UI now supports admission, bounded history, four outcomes,
separate reviewed wording, retrieval evidence and cancellation. Eight focused PostgreSQL tests
and a real create/inspect/cancel/denial browser journey pass; mobile/desktop screenshots were
inspected. Checkpointf48597b is pushed; hosted CI34426506103 passed.
Current: frozen batch preparation/collection now admits all30 cases in new workspaces and
preserves fixed four-pipeline denominators. The real run prepared118 requests with no collection
errors; two system cases completed with clarification_needed. Seven unit tests and independent
source review pass. Runner checkpointacede51 is committed/pushed; hosted CI34427298842 passed.
Current: frozen generation rubric and source-bound scorer are implemented. Ten regressions
pass; independent review closed invalid-batch/configuration false-pass findings. The real
unfinished batch retains120 observations and zero reviewed successes, with all targets false.
Scorer checkpointe10c2ae is pushed and hosted CI34428243871 passed. Twelve contributions for
en01–en03 are saved and independently reviewed. Nine source-backed responses satisfy those cases;
three direct answers preserve uncertainty but omit the required policy facts. Full120 observations
remain counted and no pipeline passes its full-batch gate. Further batch filling is paused.
Demo verified in native Chrome: real handbook retrieval, visible workflow/model records, exact
citation inspection, development draft submission, administrator edit/approval and completed result.
See the [short demo guide](DEMO.md) for the verified result and operating boundaries. Chrome is
available for user exploration; do not overwrite an in-progress user draft to restore the demo.
Next: address concrete demo blockers found during use; further corpus work remains paused.
External provider dispatch/accounting and broad release gates are deferred beyond this demo.
[Timeout cleanup](plans/completed/m6-command-timeout.md) retains Windows evidence and hosted
run34373738322 passed all five jobs, including POSIX cleanup; evidence is revision-specific. Keep RAG tuning deferred. The previous
window checkpoint records the earlier stop; it does not impose a current deadline.

[REBUILD_GOAL](REBUILD_GOAL.md) and [release plan](../REBUILD_PLAN.md) own the goal and scope;
[ACCEPTANCE](ACCEPTANCE.md) owns gates. This file routes current work, not historical execution.

## Latest verified checkpoint

- Startup dependency repair: final7 focused tests pass; the real child reached recorded dispatch
  in1.422s under its unchanged20-second deadline. Original timeout and the extraction's missing
  Job-model registration failure remain in the [repair record](plans/active/m6-retrieval-startup.md).

- M5 request contract:25 initial focused PostgreSQL checks,9 final contract/recovery checks,
  frontend build/42 tests and one real development browser approval journey pass. Exact evidence
  and preserved failures are in the [M5 record](plans/active/m5-generation-pipelines.md).
  Full local regression timed out at420s with a cold child-startup failure; it is not a pass.
  That checkpoint introduced schema0015; development now runs0016 for comparisons.
  Packaged release remains at its prior checkpoint.

- Earlier packaged-admin checkpoint: **fd18e50**, packaged admin journeys and test cleanup,
  committed/pushed. Hosted CI34365353115 passed all five jobs, including real PostgreSQL,
  frontend browser checks and packaged-release smoke. The earlier window handoff changed documentation only.
- Recovery checkpointfb29b6f CI34362786364 passed; original backups/databases remain preserved.
- Status-navigation checkpointf1cb7ad is committed/pushed;53 preparation checks passed at
  `.artifacts/m0/prep-20260909T142552861669Z`.
- Packaged admin/session/import/inbox run:9 passes at `.artifacts/m6/release-admin-20260909`.
  After settings-test cleanup and promise-handling repairs, both settings cases pass at
  `.artifacts/m6/release-settings-final-20260909`. Other eight cases are unchanged; no full
  security/expiry/nativezoom claim. Independent source and documentation reviews are closed.
- Final administration preparation:53 passes at `.artifacts/m0/prep-20260909T144034446438Z`;
  Chromium environment check passes at `.artifacts/m0/browser-20260909T144047776655Z`.
  The ignored local `.artifacts/m6/window-checkpoint-20260909T1458.json` records final revision,
  CI and stop observations when present; its absence on a new checkout is not an error.
- Independent safety and documentation reviews closed with no actionable findings.
- All71 backend units pass: `.artifacts/m0/backend-20260909T141032167323Z`.
- All53 preparation checks pass: `.artifacts/m0/prep-20260909T141735149948Z`.
- Saved restore: `.artifacts/m6/restore-saved-20260909T141055Z`;23 tables match the old manifest.
  Source/clone separation and unchanged original hashes pass in
  `.artifacts/m6/saved-backup-proof-20260909/verification.json`.
- Default fresh restore also passes: `.artifacts/m6/restore-20260909T141337Z`.
- Previous backup checkpoint338a88c CI34360979852 passed; packaged-workbench checkpointfb2db23
  CI34360000750 passed. [Saved-backup record](plans/completed/m6-saved-backup-restore.md).

The latest passing explicitly recorded local full PostgreSQL wrapper result is155 passes from the
Quality slice: `.artifacts/m0/integration-20260909T122535921561Z`. Later hosted CI also runs its
configured integration suite; its count is not restated here. Backup tests and restore runs
verify their changed boundary, rather than providing a new local full application regression.

## Implemented behavior and evidence map

| Area | Current implemented/verified boundary | Owning evidence |
| --- | --- | --- |
| Identity and isolation | Sessions, workspace roles, server-enforced permissions and denial tests | [Foundation](plans/active/m1-foundation.md), [acceptance](ACCEPTANCE.md) |
| Knowledge and retrieval | Real TXT/Markdown ingestion, versions, local embeddings, pgvector, BM25, reranking and exact-source inspection | [Retrieval](plans/active/m2-real-retrieval.md), [RAG design](RAG.md) |
| Processing and review | Real persisted LangGraph, attributed development handoff, cited draft, approve/edit/reject, clarification, cancel/retry and history | [Human review](plans/completed/m3-human-review.md), [packaged journeys](plans/completed/m6-release-workbench.md) |
| Administration | Searchable paginated inbox, JSONL imports/labels, version management, language settings and usage | [Imports](plans/completed/m4-message-import.md), [settings](plans/completed/m4-settings-usage.md) |
| Quality | Registered historical five-strategy retrieval results, failed cases and authorized traces | [Historical evaluations](plans/completed/m5-historical-evaluations.md) |
| Local release | Built assets, isolated migrated stack, actual browser journeys and hosted packaged smoke | [Packaging](plans/completed/m6-local-release.md), [CI](plans/completed/m6-release-ci.md) |
| Small-team workload | Five operator sessions plus background ingestion, trace inspection and cancellation | [Profile](plans/completed/m6-small-team-profile.md) |
| Recovery | Standalone backup, fresh and saved-snapshot parity, new restored ASGI/worker request | [Backup](plans/completed/m6-standalone-backup.md), [saved restore](plans/completed/m6-saved-backup-restore.md) |

Packaged workbench evidence covers ten distinct cases across retained initial/focused runs,
not a single all-green ten-case suite. EN approval/copy, JA editing/copy and ZH rejection/history
use real retrieval and explicit fixed development drafts. Five sessions prove overlapping admitted
work, not five simultaneous inferences or a production throughput/SLO claim.

## Runtime and provider boundary

Development: `asi-rebuild-v1`, app8010/frontend5180/PostgreSQL5440. Packaged release:
`asi-release-v1`, app8011 with separate database/model volumes. Revalidate live processes before
operating on them; these names are configuration, not a perpetual health assertion.
[Architecture](ARCHITECTURE.md) and [runbook](RUNBOOK.md) own topology, setup and commands.

Local CPU embedding/reranking and retrieval are real. Configured ordinary runs use local-model
inference; existing manual waits, frozen comparisons and offline tests use attributed development
contributions. No paid/cloud generation
adapter/API call or paid billing has been verified. Do not present handoff duration as inference
latency, exact quote matching as semantic entailment, or mock output as model quality.

## Open gates and retained uncertainty

- M5: four attributed development pipelines, their administration view and full-corpus
  preparation/collection and an attributed-review scorer are implemented; full-corpus responses
  and semantic reviews remain incomplete. Quality also shows
  historical retrieval reports. `comparable` only means unchanged corpus/not cancelled, not
  complete or correct outputs. Contributions remain in the development CLI.
- External generation-provider integration, generation accounting and semantic support/language/
  routing quality remain incomplete. No paid API access/spending authority is available. Authorized local inference supplies
  local-live evidence; external-provider verification stays separate and unverified.
- Broader release security/session and process-kill/recovery matrices remain incomplete.
- Native Chrome200% zoom is unverified. Computer Use stopped at13:18 UTC because it could not
  identify the browser URL confidently enough for policy enforcement; keep it stopped for this
  turn. [Native-zoom record](plans/active/m6-native-zoom.md) preserves the interrupted harness.
  Responsive widths, CSS doubled content and headless browser tests do not replace native zoom.
- Saved restoration proves trusted local API/worker recovery, not restored browser/network
  deployment, schema upgrades, inherited-action replay, generation quality or a recovery-time SLA.
- Earlier intermittent child/claim/clock failures remain unresolved where recorded. Passing
  follow-ups did not establish their root cause. Existing AnyIO/model deprecation warnings remain.
- RAG tuning is deferred: retain `.artifacts/rag-hardening/deferred-capacity-20260909`. No50k-chunk
  retrieval capacity pass; the earlier50k-message inbox check is a separate boundary. The measured
  default is vector-rerank; do not claim hybrid superiority or silently replace the four-pipeline goal.

No full production-readiness or release-completion claim is supported. Detailed prior evidence,
failures, revisions and superseded status text are preserved exactly in
[September9 status history](STATUS_HISTORY_2026-09-09.md) and the linked execution records.
