# Remaining generation-provider and evaluation work

## Assessment, not implementation

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
