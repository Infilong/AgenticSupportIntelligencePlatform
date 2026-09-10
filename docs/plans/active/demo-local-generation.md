# Automatic multilingual demo answers

## Execution brief — 2026-09-10

User outcome: ordinary EN/JA/ZH questions produce a useful cited draft without a manual
development handoff. The user approved local model inference and downloads if needed.
Keep real retrieval, current permissions and administrator review. No broad RAG redesign,
paid API, new infrastructure or exhaustive corpus work.

Observed: both `你们的客户政策` and `你们的团队结构` retrieved sources but the graph
unconditionally interrupted for a manual contribution. Team evidence describes product teams
and workspace roles, not a corporate organisation chart. Answers must preserve that distinction.

Approach: maintained LangChain Ollama adapter, existing local Qwen model, bounded source-only
prompt, persisted machine attribution and model ledger, existing LangGraph review continuation.
Persist provider selection in the graph; leave existing manual handoffs/comparisons unchanged.
No human attribution for model output. Only local endpoint configuration, no cloud fallback.

Verify: focused provider and real PostgreSQL graph/review/fence tests, EN/JA/ZH real local
questions (including the user's two messages), Chrome answer/citation/workflow display,
independent review, lint/build and relevant preparation checks. Preserve original attempts;
retry the user's messages as linked attempts after the integration is running.

Root owns implementation; independent reviewer checks attribution and publication fences.

## Findings and scoped fixes

The installed vision model was slow and returned invalid JSON. The downloaded 3B text model
was faster but gave weak policy summaries; the active demo uses `qwen2.5:7b`. Initial schema-mode
Japanese outputs contained malformed JSON; the same request passed with Ollama `format=json`.
Pydantic shape/size validation and server-owned source-ID validation remain mandatory. Raw failure
evidence is retained under `.artifacts/demo-chinese-review/`, including `ja-7b-raw.json` and
`ja-json-mode.json`. No string-repair heuristic or canned policy answer was added.

Independent review found late inference could overwrite a reconciled uncertain ledger state.
Both completion paths now update only a still-started call; success must affect exactly one row.
Late success/failure tests preserve uncertainty and block publication. Reviewer closed the finding.
An empty model source selection now returns insufficient evidence instead of a technical failure;
it remains an unverified model response, not a cited or approved answer.

Verification so far: final nine focused PostgreSQL cases pass in35.07s at
`.artifacts/m0/local-generation-api-20260910T030237978867Z`; earlier15-case local/manual suite
passed55.25s. Ten provider units and Ruff/178-file formatting pass. Frontend build and47 tests
pass before the final explanatory text correction. Native Chrome displayed automatic Chinese
drafts and the local generation node, model name, input tokens, duration and external charge.
Final JSON-mode runtime: all six ordinary questions reached cited drafts with local Qwen7B.
Both original Chinese messages have linked attempts; original data/failures remain preserved.
English/Japanese equivalents also produced same-language answers. Run times6.1–18.3s are
observations, not an SLO. Exact run IDs/results are in
`.artifacts/demo-chinese-review/json-mode-cases.json` and `*-json-mode.json`.
Native Chrome inspected the final Chinese answer, corrected review guidance and local generation
details. Screenshot `chrome-local-answer.png` was visually inspected; no overlap was observed.
The model supplies partial policy summaries; this is not complete corpus or semantic-quality proof.

Final independent documentation review verified the six saved local-model runs and nine-case
PostgreSQL evidence and renewed the five affected receipts. Final preparation56 tests pass16.33s
at `.artifacts/m0/prep-20260910T031832113643Z`; final10 provider units pass1.15s and Ruff/format
checks pass. The demo fix is complete; further RAG refinement remains deferred.

Post-checkpoint Chrome verification: run `b80d0bb6-2a43-430d-abe9-e697d0d3b240`
was approved after inspecting both saved source passages. The worker completed publication;
an authenticated API check confirmed unchanged draft, citations and model-call IDs, the exact
approved response, and the recorded administrator reason. Evidence:
`.artifacts/demo-chinese-review/en-team-approved.json` and `chrome-local-approval-history.png`.
This closes the real local-generation-to-approval browser journey; no customer message was sent.
Source checkpoint `b967cbeb50961055ed14685f8fa88b19b16e5363` passed all five jobs in hosted
CI34432941130, including real PostgreSQL regressions, frontend and packaged-release smoke.
That CI smoke retains its configured manual mode; local inference proof comes from the native
demo evidence above, not from the packaging check.
