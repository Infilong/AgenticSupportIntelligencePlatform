# Generate the RAG evaluation baseline from retrieved evidence

## Goal
Replace hardcoded refund answers with bounded evidence-backed provider execution and accounting.
## Context
vector_rag currently calls hybrid retrieval and returns a fixed 30-day policy without a model call.
## Requirements
Use vector-only ranking, current workspace/language-filtered evidence, bounded snippets and the
configured evaluation_vector_rag provider. Record usage/failures; no-source cases skip generation.
Mock mode must extract supplied evidence and be documented as a deterministic fixture.
## Non-goals
Semantic embedding replacement, factual entailment grading, spend reservations or paid verification.
## Acceptance Criteria
An updated 7-day policy cannot yield the old canned 30-day answer. Provider execution is ledgered;
missing sources route to review without a call; prompts are bounded and citations link supplied evidence.
## Plan
Add a small baseline-generation module. Extract the RAG branch/helpers from the oversized runner.
Add a validated retrieval strategy option while preserving the default hybrid API behavior.
Add multilingual/provider/no-source/context-bound regressions and run evaluation/retrieval/agent tests.
## Verification
Reproduce the canned response, inspect final ledger/trace records, lint and source-size gates.
Rebuild the local stack and exercise the browser evaluation journey with mock providers.
## Risks
Vector ranking over mock embeddings does not establish semantic quality. Retrieved content is
untrusted data, not instructions. Citation presence is not factual support; grading remains open.
## Progress
2026-09-07: inspected the unconditional canned response and hybrid baseline mismatch.
The prior live image failed all three seven-day policy cases. The replacement passed 50 affected
tests, then seven final focused cases covering evidence bounds, no-source behavior, vector-only
ranking and uncited answers. Lint and all three rebuilt browser journeys passed (26 seconds).
Evidence: `.artifacts/20260907-rag-baseline/`. Runner shrank from 572 to 558 lines.
## Decisions
Keep the public vector_rag mode name but make its actual retrieval strategy match the name.
Keep model execution and test simulation distinct through the shared configured-provider router.
## Findings
The previous RAG branch incurred no generation cost and could answer an unrelated fixed refund policy.
An overly broad negative test matched digits inside random citation UUIDs; the corrected assertion
rejects obsolete policy phrases in each language. Failed evidence is retained alongside final runs.
## Final Result
Completed for baseline generation. New RAG evaluations generate from bounded current evidence,
record usage/cost and report only citations present in the answer. Local mock generation is an
explicit evidence-quoting fixture. Factual-support grading and semantic embeddings remain open.
