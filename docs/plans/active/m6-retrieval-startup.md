# Retrieval startup dependency repair

Root owns provider/ingestion/retrieval/population imports and focused tests; follow backend guide.
The full regression child failed before inference: retained stack in
.artifacts/m0/integration-20260909T153311707424Z/retrieval-child-stack.log shows Torch DLL loading
through retrieval→ingestion→splitting. This identifies the avoidable import path, not an OS-level
DLL delay diagnosis. An independent reviewer also found population→ingestion for SPACE.

Move the unchanged cached embeddings factory and SPACE identity to providers/local_models.py.
Both ingestion and retrieval use the same callable; preserve first-call Settings cache directory,
model/revision/vector-space string and lazy model loading. Ingestion re-exports existing names for
compatibility. No ranking, scoring, deadlines, model settings or acceptance-threshold changes.

Verify fresh-process retrieval import does not import ingestion/splitting/Torch; factory remains
shared/lazy. Run real-process retrieval ownership recovery plus related strategy/ingestion tests,
Ruff lint/format and unit/preparation checks. Preserve the original failed evidence. Require
independent source/doc review and hosted CI before claiming the regression fixed.


## Verification

- Initial extraction:73 unit tests passed42.51s,
  .artifacts/m0/backend-20260909T160044054431Z; Ruff lint/format pass.
- PostgreSQL slice initially26 passed/1 failed85.99s,
  .artifacts/m0/retrieval-startup-20260909T160116008340Z. Child imports improved to1.5s but
  ModelCall FK resolution failed because ingestion had incidentally registered Job. Added an
  explicit Job model import in usage/models.py; no queue/ingestion dependency was restored.
- Final fresh-process unit and real retrieval-recovery slice:7 passed9.84s,
  .artifacts/m0/retrieval-startup-fixed-20260909T160609883348Z. Child imports1.328s, persisted
  inference phase1.422s; terminated process and concurrent sweeps produced one uncertain trace
  and model record with unknown usage/cost. The original20-second assertion is unchanged.
  This verifies the targeted startup/ownership case; it is not a fresh full-suite pass.
- Independent review found no permission, cache/configuration or vector-space change; explicit
  foreign-key registration and identity bootstrap in the subprocess test are documented.
  No RAG ranking/tuning or model-setting changes. Final preparation and hosted CI pending.

Final local preparation:55 passed in20.788s, .artifacts/m0/prep-20260909T160918571224Z.
Ruff lint and160-file format check passed. Hosted verification is pending.
