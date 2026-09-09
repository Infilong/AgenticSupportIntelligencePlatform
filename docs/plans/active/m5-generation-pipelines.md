# Remaining generation-provider and evaluation work

## Pre-slice assessment (before the connected contract below)

EVAL/LANG/RAG/TRACE: provide four actually distinct generation pipelines while retaining the
approved keyless development workflow. This is a deep cross-boundary change; root must keep one
implementation owner and obtain independent review. Applicable backend/support/evaluation,
evals/scripts/frontend guides must be loaded for touched boundaries. No paid calls authorized.

The current generation node in backend/app/workflows/support_graph.py interrupts and later reads
an authenticated stored contribution. It does not dispatch a language model. The existing context
and citations require at least one exact source, so routing direct_llm through that support-draft
path unchanged would silently violate the no-retrieval baseline. The support default remains
vector-rerank; it is not the release plan's governed hybrid system_v1 pipeline.

backend/app/providers currently contains recorded local embeddings/reranking only. Settings only
accept mock mode at the core runtime layer; the workspace Settings API separately exposes
language configuration. model_calls has input tokens but no output-token or generation-pricing record.
Historical evaluation registration presents five retrieval strategies; it does not execute the
four generation pipelines. Keep these as explicit gaps, not green placeholders.

## Next executable slice

Design one connected recorded-generation path before implementing the four-way runner. Define
immutable request/result and prompt/context identity, maintain the attributed development handoff,
and integrate a maintained LangChain provider adapter with the existing authorization, lease,
cancellation and publication guards. No database transaction may span a provider call. Persist
dispatch attempts, actual provider usage and failures/uncertainty; unknown values stay unknown.
An API key alone must not enable paid dispatch: explicit local spending authority is separate.
Keep paid mode disabled without that authority. Cancellation fences publication but cannot prove
an already-dispatched provider stopped or incurred no charge. An uncertain-dispatch retry policy
must prevent silent duplicate generation; adapter/offline tests do not establish live quality.
Tests may inject a deterministic provider; production must not return fixture-specific answers.
Do not commit unused interfaces or call an isolated adapter complete without its connected path.

Then run the same frozen queries/settings through direct_llm, vector_rag, hybrid_rag and system_v1.
Use separate evaluation results rather than relaxing application citation/publication safeguards
for the direct baseline. Record actual retrieval strategy, context/prompt identity, generation
settings and review/routing differences. Expected answers remain evaluator-only; response content
must never be read from the scoring fixtures. Distinguish offline workflow proof from semantic
quality and preserve missing live results.

Verification must include authorization before dispatch and publication, cancellation/lease loss,
timeout and uncertain outcomes, idempotent resume, genuine per-pipeline routing and accounting,
and UI projections of real records. Review the plan before the source edit; narrow this first
vertical slice based on the current code. Packaged admin demo checks are now recorded in
STATUS. The user removed the execution deadline on 2026-09-10 (Tokyo); this remains the next
implementation assessment and does not change the goal or authorize external spending.

Independent design review agrees with this connected first path and the separate evaluation-only
direct baseline. All three clarifications above (core/workspace Settings, external cancellation
limits and disabled paid mode) are incorporated. No generation source implementation began in
the prior window; the first source slice must now be narrowed and verified within the
continuing authorized goal.

## Connected slice: attributed development request contract

Root owns backend migration/provider/support code and the existing frontend submission binding.
Persist a versioned rendered request and SHA-256 on new handoffs; retain the already stored
context/prompt/contributor/result identities. Existing handoffs stay unchanged and explicitly
report a reconstructed request. Use a maintained LangChain RunnableLambda to validate and replay
the stored contribution in the actual generation node, outside its database transaction.
No ModelCall is created for replay; no inference or pricing claim is introduced.
The exported request hash can be submitted by updated clients. Legacy clients retain the
existing context hash binding; the server validates the stored rendered request in both paths.
Check request/context/result consistency before replay and fenced publication. Preserve existing
contributor/requester checks, cancellation, sources, and checkpoint recovery. This contract is a
first connected part of M5, not completion of the external adapter or four-pipeline runner.

Verification: focused real-PostgreSQL success/tamper/revocation/cancellation/replay and migration
cases; existing support/review regression; generated OpenAPI, frontend checks and actual browser
handoff submission. Independent security review and documentation freshness precede commit.
Reference: [LangChain RunnableLambda](https://reference.langchain.com/python/langchain-core/runnables/base/RunnableLambda).


### Contract verification checkpoint (2026-09-10 Tokyo)

- Initial PostgreSQL support/safety/recovery slice:25 passed in84.20s,
  `.artifacts/m0/generation-contract-20260909T152524531646Z`.
- Extended recovery initially8 passed/1 failed: injected raw psycopg error was terminal outside
  the graph wrapper. Use the worker's actual RetryableJobError for the intended recovery seam;
  assertions unchanged. Final9 passed in29.61s,
  `.artifacts/m0/generation-recovery-fixed-20260909T153145661960Z`.
  This proves completed-checkpoint reuse and publication rejection, not process-kill recovery.
- Frontend build and42 component tests pass. OpenAPI regenerated; focused Ruff passes.
- Real development browser English policy retrieval→contribution→operator approval/copy/history:
  1 passed43.0s, `.artifacts/m5/generation-contract-browser-final-20260910`.
  First anchored filter selected no tests; retained separately. Inspected draft/history images.
  Trace request-binding-proof.json confirms run68e97181-8e63-4ebe-b123-1c0af4d9a510 submitted
  request hash5432b9ff557a4489685529b5ca57e4807a60d7e479a08ffc117b70b20ff500d6 with202.
  Bounded15:32–15:34 UTC logs:54 HTTP200,3 HTTP202,1 HTTP204; three jobs succeeded, no error
  markers. Client-injected503 is not a backend error. Manual draft is not generation quality.
- Full local regression did not pass: `.artifacts/m0/integration-20260909T153311707424Z`
  hit420s, with one failure in collected-position107: real_process_kill_releases_ownership_and_
  concurrent_sweeps_converge. Saved child phases show launcher only, no trace/model dispatch;
  stack is in cold retrieval/ingestion/splitting imports. This remains an unresolved startup
  deadline failure, not proof of a new generation-contract defect or a clean full regression.
  subprocess.run killed its launcher but orphan pytest descendants retained the pipes. Root
  revalidated their exact command/basetemp and stopped only PID34792 and descendant18712,
  allowing timeout evidence to finish. Existing app/release/archive databases preserved.
- Independent security reviewer found no remaining source issue and accepted both added recovery
  tests. Full provider dispatch and four pipelines remain incomplete. Next fix the evidenced
  command-timeout descendant cleanup, then resume the M5 evaluation/provider work.

Preparation after independent review:53 passed in9.871s, .artifacts/m0/prep-20260909T154700956254Z. This appended evidence note changes no application or mapped contract source.


## Next execution brief: one resumable four-pipeline comparison

Root remains the single implementation owner. EVAL/TRACE/LANG: add an administrator-created,
workspace-scoped comparison for one persisted question/language, with four immutable pipeline
records. No API key or paid dispatch; use attributed development transport. Ordinary support
requests keep their default strategy and publication safeguards. Implement the connected case
before extending the runner to the frozen30-case corpus and its per-language scoring.

- direct_llm: no retrieval invocation or trace, empty evidence, evaluation-only prompt/response
  allowing no citations. Never route it through the support cited-draft submission endpoint.
- vector_rag and hybrid_rag: real declared retrieval strategies, bounded context, distinct trace
  identities and the same versioned generation settings. Retain missing/failed evidence explicitly.
- system_v1: actual governed support/LangGraph path with immutable server-selected hybrid
  configuration, existing clarification/source/cancellation checks and human review. Link its
  real support run; do not imitate that workflow inside an evaluation-only helper.
- Persist admission/jobs atomically, request/context hashes, contributor and response identity,
  attempts/failures and terminal outcomes. Recheck membership and sources before protected
  context export, response acceptance and publication. Bound lists and comparison admission.
- Generation receives only whitelisted question/language and retrieved source data. Case IDs,
  expected facts, rubrics and scoring inputs stay evaluator-only. New schemas reject extra fields.
- Provide a working CLI/API create→request export→attributed submission→resume/read flow.
  Reuse existing session/CSRF and workspace enforcement; no client-selected arbitrary graph state.
  A comparison's manual outputs prove plumbing, not external inference or semantic quality.

Review design before source edits. Required evidence: direct makes zero retrieval calls; other
pipelines retain correct real strategy traces; system alone follows review/early-exit workflow;
request-bound idempotent resume, changed-evidence and cancellation denial, foreign-workspace and
revoked-member denial. Then run one real local comparison through the CLI with actual retrieval.
Keep the still-required external provider/accounting path and full30-case comparison visible;
this executable slice does not redefine M5 completion.


Independent design-review guardrails for that next slice:
- Keep initial contributions separate from edited/approved system responses. Report both stages;
  never score a human-revised system answer as if it were the original generation.
- vector_rag uses vector; hybrid_rag and system_v1 use hybrid with matching retrieval/context
  limits. Persist exact configurations and active corpus/version fingerprints. A changed corpus
  during resumable preparation invalidates comparability explicitly; do not silently mix versions.
- Baseline RAG with no sources records terminal insufficient_evidence; preserve it in denominators.
  Direct remains a source-free attributed request. Incomplete/failed pipelines are never dropped.
- Comparison cancellation fences pending jobs and the linked unfinished support run. Already
  completed outputs remain immutable history; cancelled comparisons reject further request export
  and submission regardless of matching hashes.
- Each generation export contains only that pipeline's rendered request, never other pipeline
  answers, review edits or scoring fixtures. Full admin comparison inspection is a separate read.

### Single-case implementation checkpoint

Migration0016 and modules/comparisons connect atomic four-way admission, three baseline worker
jobs and a real linked hybrid support graph. CLI generation_cli.py uses authenticated local
API create/list/read/export/submit/cancel commands, without loading scoring fixtures. Frozen
system runs reject new attempts; users create a new comparison to alter input or retry.
Independent security review found empty system citations could raise an internal validation
error; fixed with explicit422 before conversion and covered in the success regression.
Second review found no further actionable source issues.
First focused run:5 passed/2 failed, retained at
`.artifacts/m0/generation-comparisons-20260909T162858038856Z`. Test setup reused a pre-login
CSRF token and expected403 for a foreign workspace's deliberately concealed404. Fixed tests
without changing server authentication behavior. Final17 comparison/contract checks passed
83.71s at `.artifacts/m0/generation-comparisons-fixed-20260909T163215511915Z`.
Ruff lint and169-file format check passed; OpenAPI regenerated. At that point, real CLI
demonstration and preparation/documentation review were pending. This did not complete M5.

Live demo surfaced a fresh-worker registration defect: direct/vector first attempts retried,
then succeeded after a support job registered support_runs. A standalone import reproduced
NoReferencedTableError for Pipeline.run_id. Explicitly register SupportRun from comparison models;
the new subprocess unit test passes2.67s. Retain the first demo's retry evidence rather than
claim first-attempt success. The new CLI's per-command logins also reached the existing10-login
throttle; direct/vector contributions were accepted, hybrid/system still pending. Preserve the
security throttle. At that point, reusable local session support was needed to complete the demo.

Session support is now implemented with an explicit ignored .artifacts path, server identity/CSRF
validation and renewed authentication only after expiry. Four session/cold-import tests pass
2.75s using a fresh workspace-owned basetemp. Initial session tests hit the known shared Windows
pytest temporary-directory permission error before test bodies; preserved in tool output.
The full local PostgreSQL wrapper reached126 displayed passing cases, then its420s command
timeout: `.artifacts/m0/integration-20260909T164323903597Z`. No failing assertion was displayed,
but this is incomplete verification, not a full-suite pass. Frontend production build passes.
`comparable` denotes corpus identity and cancellation only; incomplete/failed pipelines remain
visible and must be retained in evaluation denominators. Semantic quality remains not_verified.

Actual development demo d2d7f2e6-087e-4699-9dcd-e30b6080687c completed all four pipelines.
Evidence: `.artifacts/m5/four-pipeline-demo-20260910/` retains CLI requests/responses/final.json,
three distinct real local-CPU E5 ledgers and retrieval records, plus browser-trace.zip.
The real Playwright browser edited and approved linked support run
8e8287ef-8cb0-4153-9da2-48ba1fd6efa4; system-reviewed.png was visually inspected with no overlap,
no page errors, and original contribution visibly separated from approved wording.
Session reuse completed remaining submissions without modifying the existing login throttle.
This is a manually authored plumbing demo, not blind semantic evaluation or a live provider call.
The screenshot still offers generic added-details controls on this frozen comparison run;
the API correctly rejects attempts. Hide those controls when connecting the comparison UI.

Cold-worker follow-up: restarted only the verified idle development worker, admitted a new
comparison and read all four waiting_for_input records with attempts=1 in cold-read.json.
This verifies first-attempt preparation after the FK registration fix; no contributions were
invented for that second comparison. The original completed demo and its retry evidence remain.

Final checkpoint gates:56 preparation tests passed19.524s at
`.artifacts/m0/prep-20260909T165747962573Z`;77 backend units passed43.11s at
`.artifacts/m0/backend-20260909T165808685680Z`. All six documentation areas independently
reviewed; final security review found no blocking issue. Source and mapped documentation stayed
unchanged during these checks; this appended historical evidence note follows them.
Next: frozen-corpus runner and comparison UI, including hiding frozen-run attempt controls;
external generation provider/accounting and full release verification remain required.
