# Current status

Goal: **M1–M6 authorized and active; not complete**. Current milestone: M2.
Branch: `codex/fresh-start`. Goal starting revision: `2c292d08b5ff9d577276c8513fc53582a1ba93d4`.
[M2 execution plan](plans/active/m2-real-retrieval.md) owns current decisions and evidence;
[M1 history](plans/active/m1-foundation.md) retains foundation work.
Normal verified commits/pushes to this branch are authorized. No merge/deploy/paid API authority.
The existing unattended cutoff is **2026-09-08 17:34 UTC**; this checkpoint does not extend it.

## Verified current behavior

- Real login, sessions, workspace roles and server-enforced permissions.
- PostgreSQL jobs with claims, leases, cancellation and fenced publication; one worker.
- TXT/Markdown originals, versions, bounded background indexing, withdrawal and restore.
- Real pinned local CPU embeddings and PostgreSQL/pgvector retrieval, followed by a measured
  local multilingual reranker over 20 authorized candidates. No external API needed for search.
- Knowledge upload/search/source inspection UI, including exact cited versions and offsets.
- Persisted model identity, status, locally counted tokens, duration and zero external charge.
- The UI labels **responses** as simulated; retrieval is real.

## Current verification

| Boundary | Evidence |
| --- | --- |
| Frozen retrieval | 26/26 evidence cases; 27/27 groups; EN 8/8, JA 9/9, ZH 9/9; warm p95 2.5 seconds; zero forbidden leaks; foreign request 404 |
| Backend | 16 unit tests and 45 real PostgreSQL tests pass |
| Harness | 19 preparation checks pass |
| Knowledge UI | Two real desktop/mobile journeys pass; source/search screenshots inspected |
| Frontend | TypeScript/build and two component tests pass; baseline browser suite also passed |
| Models | Explicit preparation/inference passed for both pinned local models |
| Graph prerequisite | Supported LangGraph/PostgreSQL interrupt and failed-node recovery pass after connection reconstruction; application workflow remains pending |
| Git/CI | Retrieval `01ee83f`, CI `34254935876` passed; UI clarification `1a0e0e6`, CI `34255679023` passed |

Final stable retrieval evidence: `.artifacts/m2/retrieval-eval-20260908T170142Z`.
Final label/browser evidence: `.artifacts/m2/provider-label-rebuilt-ui`.
Detailed command artifacts and prior failures are retained in the M2 execution record.
LangGraph `1.2.11` and PostgreSQL checkpointer `3.1.2` are installed in the rebuilt runtime.
Latest PostgreSQL evidence: `.artifacts/m0/integration-20260908T172545791661Z`.
The real retrieval smoke still passes after dependency installation; the full frozen quality
measurement above belongs to the earlier retrieval snapshot and was not rerun for this lock change.
No full production-readiness, generated-answer quality or completed release claim is supported.

## Failures and limits

- Original multilingual ranking failed (20/26 cases); the unchanged frozen corpus now passes
  after measured reranking. This set was used during tuning, not held out for generalization.
- One revocation test failed initially. An indexed-source precondition was added; isolated
  and full stable reruns pass, but the original intermittent cause is not established.
- Early checks whose source files changed mid-run remain invalid as overall evidence even
  when individual tests passed. Final verification ran against an unchanged snapshot.
- Chrome lists the app tabs, but interactive screenshot capture timed out. New visual proof
  comes from the actual application browser suite; do not call it a completed Chrome demo.
- Upstream AnyIO and model cache-argument deprecation warnings remain visible.
- Synchronous model/retrieval records abandoned by a process crash need reconciliation.
- Generated responses, message processing, LangGraph checkpoints, review, imports, complete
  observability, comparative evaluation and restoration remain incomplete.

## Next connected slice

Persist an original customer message and processing attempt, run real retrieval, pause for an
explicit Codex-assisted development answer, then validate and persist a cited draft. Use the
planned LangGraph/PostgreSQL checkpoint path; keep handoff waiting separate from human review.
Recheck permissions and source validity on resume. Never import evaluation expected answers
as runtime responses, invent API usage, or treat citation-ID validity as semantic support proof.
Continue within the existing goal and time boundary; missing APIs do not block real local search.

## Preserved history

The old implementation/data/services and archive branch remain untouched. Foundation and
knowledge milestones are documented in the owning execution records rather than repeated here.
Future work must revalidate live services before operating on them.
