# Final demo review and handoff

## Execution brief

User requests a final comprehensive review and live demo, followed by task closure.
Inspect backend safety/workflow boundaries and frontend/runtime behavior independently.
Root owns runtime verification and any necessary fixes. Fix demo blockers; document smaller
risks without reopening deferred production-quality scope or adding features.

Verify current packaged runtime health, fresh knowledge ingestion, EN/JA/ZH automatic answers,
review, missing knowledge, set-aside, cancellation and permission denial. Inspect Chrome user
journeys and traces. Preserve failed evidence and original data. Completion requires a reviewed
record of observed outcomes and limitations, not a guarantee of arbitrary-answer correctness.

## Evidence

Final live verification is in progress; artifacts are under `.artifacts/final-demo/`.


## Reviewed repairs and current live evidence

The final review found three narrow UI/test issues: the new-message form stayed editable during
submission, Settings incorrectly described all local outputs as review drafts, and the settings
browser test assumed the previous language default. Root disabled pending edits with a component
regression, corrected local routing copy, and updated the browser assertion to Match question plus
persisted punctuation fallback and server-reported provider availability.

`.artifacts/final-demo/report.json` records six passing expected outcomes: cited EN/JA/ZH answers,
policy review, missing-support intervention and set-aside. Fresh English knowledge ingestion
supported a Chinese answer giving12 days. Viewer403, foreign404, CSRF403 and cancellation were
observed. These bounded checks do not establish arbitrary-answer correctness or full reliability.
Frontend49 tests passed8.64s and build passed; packaged startup
`.artifacts/m0/release-up-20260910T065805671279Z` passed.

Independent backend review found no P0/P1. It retained a P2 in recorded_embeddings: a late
embedding result can overwrite an uncertain ledger outcome after ingestion lease reclaim;
domain publication remains fenced. This accounting/recovery risk is explicitly deferred under
demo acceptance. Do not claim the race is fixed or full reliability established.

Chrome human-clarification and settings browser verification remain underway. The initial
settings browser attempt failed because its default browser cache was missing; a rerun with the
documented cache is pending. Preserve this environment failure; it is not an application pass.


## Final browser evidence and disposition

`.artifacts/final-demo/settings-browser-final` passed two browser tests in7.4s across
360/768/1440px; the fallback setting was restored. The initial cache failure remains preserved.
Chrome recorded human clarification on run c2830b92-a672-47d2-a19b-a8cf37a60edb, completed after
recording the clarification request while the original draft stayed unapproved; screenshot
`.artifacts/final-demo/clarification.png` was inspected by the coordinator.

Chrome also inspected the Chinese workflow's real LangGraph stages and successful E5/reranker/
Qwen7B calls:1783 input tokens, about2.26s generation and zero external charge. The recent
15-minute API/worker error filter was empty; this is a bounded observation, not an exhaustive
log audit. The last newly submitted Chrome question was still pending at the observation boundary
and is not counted as an additional completed case.

Current frontend49 tests/build and two settings browser tests pass. The132 backend-unit result
belongs to the preceding language repair, not a fresh full backend regression for this review.
No full semantic benchmark pass or repair of the deferred P2 ledger race is claimed. The final
review is complete for the user-approved demo scope; this record moves to completed. Remaining
strict quality/release gaps stay deferred. Final documentation review and preparation checks pass.


Final rebuilt-UI Chrome run8a95213b-13f8-430a-bb2f-157d9decebd7 subsequently completed/answered
with the correct Chinese12-day answer and a citation to the newly ingested English policy.
`.artifacts/final-demo/final-answer.png` was visually inspected by the coordinator without
overlap. The user tab is marked as the deliverable and the app remains running. Earlier pending
observation is superseded by this result; no broader benchmark or production claim is added.

Final preparation `.artifacts/m0/prep-20260910T070423987472Z` passed 56 tests in 16.097s.
Documentation links, diff whitespace and reviewed source fingerprints also passed.
