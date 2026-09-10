# Automatic answers and intervention routing

## Execution brief

User-authorized on 2026-09-10: supported routine questions must receive usable automatic
answers; genuine exceptions require review; missing support needs intervention; spam and
meaningless/out-of-scope inputs can be set aside. Then complete M5/M6 against the remaining
acceptance contract. This supersedes the earlier blanket administrator-review demo rule.
No paid API, public deployment, archive changes or deletion of existing attempts is authorized.

Complexity: deep, because routing changes finalization and review authority. One implementation
owner; independent read-only source/security and documentation review. Gates: ROUTE, REVIEW,
RAG, LANG, TRACE, EVAL and M6 release checks. Root and relevant backend/frontend/docs guides apply.

Observed: the ten-question smoke produced six factual drafts and four abstentions, but every
cited answer is marked unclassified and waits for admin approval. This is an orchestration gap,
not a reason to add more retrieval machinery. Existing evidence is preserved under
`.artifacts/demo-ten-questions/`.

## Implementation and verification

1. Add explicit local-model answer/review/missing/irrelevant classification with bounded
   source validation and server-side conservative routing. Automatic results are machine
   answers, never fabricated human approvals. Preserve old/manual and comparison attempts.
2. Make missing evidence actionable without allowing approval of an unsupported answer;
   retain clarification/retry and discard irrelevant messages outside the attention queue.
3. Render distinct outcomes and route explanations in inbox, response and workflow.
4. Verify actual EN/JA/ZH supported, exception, missing, ambiguous and irrelevant cases;
   run focused PostgreSQL permission/cancellation/source/replay checks and browser journeys.
5. Independently review, repair, update owning docs/freshness, commit/push and check CI.
6. Audit remaining M5/M6 gates against actual evidence; finish authorized checks without
   substituting this routing smoke for full milestone completion or claiming paid-provider proof.

Success requires routine supported questions to be ready without human approval, review to
remain meaningful, missing evidence to request intervention, and irrelevant messages to be
retained but set aside. Preserve uncertainty; never manufacture confidence or missing facts.

## Focused verification checkpoint

Sixteen focused PostgreSQL cases pass in55.29s at
`.artifacts/m0/demo-routing-api-20260910T044506954108Z`;14 provider units and frontend build/48
tests pass. Independent source review closed the conservative-fallback finding. These are
focused software checks, not complete live semantic or M5/M6 evidence. At this earlier checkpoint, actual routing cases
under `.artifacts/demo-routing/case-*.json` were still running; final results follow below.
Owning documentation now records the user-authorized four outcomes and resumed M5/M6 scope,
preserving earlier draft-only demonstrations and unchanged acceptance thresholds.

## Actual local routing checkpoint

Saved `.artifacts/demo-routing/final/case-01.json` through `case-10.json` show four completed
`answered` results (EN/ZH plan limits and JA export/ownership), two `policy_review_required`
waits (refund/deletion), and four `insufficient_evidence` intervention waits. Weather and
photosynthesis remain conservatively routed to human intervention; this is an observed
classification limitation, not a complete unrelated-topic pass. Six separate EN/JA/ZH noise/spam
cases at `.artifacts/demo-routing/noise-01.json` through `noise-06.json` all completed/set_aside.
Original attempts, retrieval evidence and failures remain preserved.

Initial cases7/9/10 failed ValidationError on empty-answer abstention; diagnostic-raw-07.json
retains the reproduction. The provider now permits a nonempty reason as the answer only for
missing/irrelevant decisions, strips their unrelated selected citations and retains model_output.
No canned factual answer or JSON string-repair was added. Independent source review closed the
fallback P1 and found no P0/P1 in normalization. Final16 provider units passed1.38s; Ruff and
182-file format checks pass. The earlier16 PostgreSQL/55.29s result predates normalization.
Final frontend build passes; earlier48 tests passed, with the final rerun still pending.
Chrome inspected automatic EN answer/source and missing-support controls without approve/edit;
first screenshot capture timed out and is not a successful screenshot claim.

After checkpoint, finish M5 through a versioned actual-local four-pipeline execution/evidence
path, then the agreed M6 release checks. Preserve the frozen development reports and targets;
never pass local machine outputs off as attributed development contributions. This bounded
smoke does not establish full-corpus semantic quality, complete regression or paid-provider proof.

Final UI verification: frontend build and48 tests pass9.79s. Chrome screenshot retry succeeded;
`.artifacts/demo-routing/chrome-missing.png` and `chrome-set-aside.png` were visually inspected
by the coordinator. Accessibility inspection confirms no review controls on set-aside; automatic
EN answer and exact source quotation were inspected separately. The first capture timeout
remains a failed capture, not erased or counted as success.
