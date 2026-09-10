# Match response language to the question

## Execution brief

Narrow user-authorized bugfix after demo acceptance: Chinese questions were saved as English
because the composer preselected the workspace default. Default new manual-message input to
`auto`/“Match question”; resolve EN/JA/ZH server-side from the question's script and store the
resolved language. Preserve explicit overrides and existing messages/import contracts.

Root owns source/runtime checks; documentation agent owns this record and relevant owning prose.
Follow root, backend/support, frontend and documentation guides; preserve others' edits.
No reopening M5/M6 or deferred quality/release work. Acceptance: LANG and message admission.

The deterministic heuristic prefers Japanese kana, then Chinese Han, then English Latin letters;
otherwise use the workspace language. Han-only Japanese is ambiguous and can be explicitly
selected. This is script detection, not comprehensive linguistic classification. The generation
instruction translates evidence facts into the requested answer language while source quotations
remain original for verification. No model call is needed to select the default language.

Verify auto/default and explicit override admission, workspace fallback, EN/JA/ZH and ambiguity,
then actual browser/API behavior and affected provider/frontend checks. Retain failures and
record exact evidence before claiming the repair verified. Final verification is pending.

## Verification checkpoint

Chrome submitted the user's exact “删除账户确认” with Match question. Run
4fa81964-e450-4dd9-be8b-1659c91d9b43 completed/answered in Chinese. Its DELETION-REQUEST source
was English-only Small-team-handbook-1788958722107.md; the quotation remains English while the
answer is Chinese. The coordinator visually inspected `.artifacts/language-matching/chinese-answer.png`.
This verifies this language flow, not execution of an account deletion or broad semantic quality.

21 focused units passed1.28s; three PostgreSQL checks passed5.02s at
`.artifacts/m0/question-language-20260910T062235689193Z`. Frontend49 tests passed14.82s and build,
lint/format checks pass. Independent reviewer closed the inherited-schema P1 with no remaining
P0/P1 finding. Release startup `.artifacts/m0/release-up-20260910T062517918239Z` passed; the prior
062259538949 attempt failed its source-change-during-build check and remains preserved.
Full units initially showed97 passes and35 temporary-directory permission setup errors; a new
workspace-basetemp rerun subsequently passed132 tests in45.01s with one existing Starlette
deprecation warning. Do not report that initial run as passed.

The narrow runtime repair is verified and this record moves to completed. Final units,
independent review and documentation freshness checks pass; deferred M5/M6 gates are not reopened.

Final full backend units:132 passed45.01s using fresh workspace basetemp. No assertions were
weakened; the earlier permission setup errors remain historical failures.

Preparation at `.artifacts/m0/prep-20260910T063026392254Z` passed all 56 tests, but its wrapper
rejected concurrent documentation changes. That failed snapshot remains preserved; rerun the
unchanged checks after documentation writes stop before committing.

Stable final preparation `.artifacts/m0/prep-20260910T063157569709Z` passed 56 tests in
19.952s with wrapper exit 0. This final evidence note changes no source or acceptance assertions.
