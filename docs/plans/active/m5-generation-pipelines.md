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
