# Mock retrieval relevance
## Goal
Stop random hash similarity from contributing to default support evidence relevance.
## Context
Default hybrid scoring assigns 35 percent weight to SHA-derived mock vectors with no semantic meaning.
## Requirements
Default retrieval with mock embeddings uses lexical scoring and reports that strategy honestly.
Unrelated EN/JA/ZH evidence cannot gain score from a matching mock vector. Preserve isolation,
current-version filtering, citations, traces and explicit vector evaluation semantics.
## Non-goals
Semantic embeddings, lexical synonym support, production vector database ranking or paid calls.
## Acceptance Criteria
Default mock ranking ignores vectors; API traces identify lexical strategy and omit vector score.
Relevant multilingual journeys pass; no-source cases remain reviewable. Explicit vector baseline stays distinct.
## Plan
1. Reproduce nonsemantic score inflation with controlled vectors.
2. Select lexical strategy for the default mock provider and avoid query embedding calls.
3. Update score-contract tests; run backend and live journeys; record limits.
## Verification
Deterministic pytest and existing multilingual browser/API suite. Preserve evidence in
`.artifacts/20260907-mock-retrieval/`.
## Risks
Threshold outcomes change because a false signal is removed. Lexical overlap cannot establish
semantic relevance; clients must tolerate an accurately reported lexical strategy.
## Progress
2026-09-07: inspected SHA-derived embedding and weighted scoring; added score regressions.
Four failures reproduced; lexical default implemented. 44 affected tests and nine live journeys
passed. The first full suite found one failure (304 passed): singular refund queries missed plural
source wording after the synthetic signal was removed. Added conservative English plural
normalization and regressions; rerunning the full suite and live journeys. Budget tests unchanged.
## Decisions
Keep explicit vector baseline as simulation; do not label lexical fallback semantic retrieval.
## Findings
A perfectly aligned mock vector gives unrelated evidence 0.35 despite zero lexical overlap.
## Final Result
Completed 2026-09-07. Default mock retrieval no longer uses hash similarity as relevance.
Plural matching preserves the budget regression. Final 309 backend and ten browser tests pass,
with lint/build/documentation/size checks. Live verification also reproduced and repaired the
unhandled workspace refresh error, with a controlled failure/recovery test. See
[testing](../../testing.md#mock-retrieval-relevance-and-refresh-recovery) for all evidence and limits.
Semantic retrieval and broader network error handling remain open.
