# Reusable full-rebuild goal

Status: activated by the user on 2026-09-08; synchronized with approved clarifications on
2026-09-09. [STATUS](STATUS.md) records current execution and constraints. This reusable goal
incorporates later user instructions; the original attached goal remains a historical record.
The user removed the execution time limit on 2026-09-10 (Tokyo). Continue within the
authorized scope without a fixed unattended deadline; retain other authority constraints.

Latest user direction (2026-09-10): deliver a successful demo product soon. Prioritize the
core user journey and fix only demo-blocking issues. Pause exhaustive corpus response/scoring
work, minor refinements and broad production hardening. M1–M6 remain the roadmap, not a reason
to delay this demo. The immediate deliverable is a usable local knowledge-to-answer workflow
with real retrieval, visible agent processing, and administrator review/intervention. Keep the
development response mode explicit. Production/live-provider gates remain deferred, not passed.

Subsequent clarification: ordinary EN/JA/ZH questions must produce automatic answers rather
than wait for development contributions. The user authorized a local language model, including
downloads if needed. Keep real retrieval and administrator review; identify local inference
honestly. Manual contributions remain available for existing handoffs and frozen comparisons.

Rebuild AgenticSupportIntelligencePlatform in this repository through M1–M6, following
[REBUILD_PLAN.md](../REBUILD_PLAN.md), the [acceptance matrix](ACCEPTANCE.md) and applicable
root/local AGENTS.md instructions.
Deliver the agreed modern EN/JA/ZH local support workbench: user data → database → real
LangChain/LangGraph and tool processing → cited results and intermediate records → authorized
administrator inspection, intervention and knowledge management. Preserve the agreed V1 scope.

For development without an API key, use explicitly attributed Codex-assisted responses behind
the planned provider contract. Parsing, chunking, local embeddings and PostgreSQL vector
retrieval must be real. Preserve the external provider integration path; development responses
do not establish external API connectivity, generation quality, billing or inference latency.
This requirement describes the intended workflow, not an already implemented generation endpoint.

Own the full loop: refine each nontrivial demand into a concise execution brief, inspect the
current code and relevant primary documentation, choose a connected slice, implement, test,
review, repair and select the next necessary slice. Continue across authorized milestones
without waiting for “continue.” Apply user corrections while preserving the overall objective.

Actively apply useful practices from OpenAI's How OpenAI uses Codex and Harness engineering:
scoped issue-like briefs, short context maps, repository-owned decisions, executable architecture
constraints, agent-readable browser/log evidence, independent focused review, environment repairs,
and feedback turned into durable tests or guidance. Select tactics that fit this small application;
do not copy unnecessary infrastructure or wait for the user to explain the articles.

Follow the [documentation freshness protocol](DOC_FRESHNESS.md) for each affected area:
inspect source-to-document mappings, regenerate factual references, independently review claims,
record the exact reviewed fingerprint and pass freshness checks before checkpointing. A review
receipt proves unchanged reviewed inputs, not semantic truth. Periodic gardening supplements
this per-change loop; it does not authorize product work beyond the current goal boundary.

Commit and push after every small coherent verified step, rather than waiting for a milestone.
Review staged changes, run affected checks, exclude secrets and temporary/build/test artifacts.
Commit designated reproducible references and API types, including
[source references](generated/source-reference.md) and `frontend/src/api/schema.d.ts`, after
regeneration and diff review. Follow owning guides for other generated files. Push to the working
rebuild branch, confirm the remote revision and inspect CI when available. Fix regressions
promptly. No force-push, main/archive updates, merges or public deployment are authorized here.

Routine implementation choices, dependencies within the approved stack, isolated development
services, deterministic tests, documentation updates and branch commits/pushes are authorized.
Preserve old services/data, unrelated edits and secrets. Request live-provider access and an
explicit spending cap when needed; keep progressing on independent offline work meanwhile.
No paid calls are authorized by possession of a key, and mock tests cannot prove live AI quality.

Verify actual UI/API/database/worker journeys, workspace isolation, model/retrieval accounting,
human review/cancellation/recovery, realistic multilingual RAG quality, responsive accessible
layouts, fresh installation and restoration against the agreed gates. Use bounded read-only
independent review where useful. Diagnose recurring failure causes and improve the harness;
never lower acceptance criteria to make the implementation pass.

Report meaningful progress and evidence while continuing. Stop only when the authorized goal
is complete, the user pauses, or required authority/a material decision blocks progress.
Preserve an exact resumption checkpoint when stopped; no fixed execution deadline applies.

Finish with the revision, remote branch, acceptance evidence, operator demo, live verification
and spending, and honest remaining limitations. Do not call the release complete with missing
required evidence, and do not manufacture additional work after the agreed contract is met.
