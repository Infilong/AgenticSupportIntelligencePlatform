# Active Prompt Runtime And Provenance

## Goal

Ensure the active workspace prompt version controls the exact LangChain prompt sent to the model provider, and make that fact independently auditable.

## Implemented Behavior

- Parse stored prompt source into explicit `system:` and `human:` LangChain messages.
- Validate supported prompt names, required variables, allowed variables, role markers, and non-empty role bodies before saving or activating.
- Use the selected active classifier prompt for both model-call planning and classification execution.
- Use the selected active drafter prompt for context fitting, model-call planning, and drafting execution.
- Persist a SHA-256 hash of the exact rendered prompt for successful and failed AI runs.
- Expose rendered prompt hashes through the graph trace API.
- Preserve historical AI rows by keeping the new hash column nullable while populating every new call.

## Responsibility Split

- `prompt_runtime.py`: prompt role parsing and variable contracts.
- `support_prompts.py`: support prompt defaults, rendering, and structured classifier schema.
- `langchain_support.py`: LangChain execution and provider invocation.
- `model_call_planning.py`: context-window planning and document fitting.
- `ai_run_ledger.py`: AI-run persistence and rendered-prompt hashing.
- `prompt_template_service.py`: prompt lifecycle validation.
- `prompt_templates.py`: HTTP 422 mapping for invalid prompt source.
- `support_agent_graph.py`: minimal active-template wiring.
- `0025_ai_run_rendered_prompt_hash.py`: schema migration.
- Focused test modules: provider capture, validation, provenance, and API-to-graph integration.

## Verification

- `uv run ruff check app alembic tests`: passed.
- `uv run alembic heads`: one head, `0025_ai_run_prompt_hash`.
- Full backend suite before final extraction: 191 passed.
- Affected suite after ledger extraction: 53 passed.
- Final prompt execution and provenance suite: 14 passed.
- `git diff --check`: passed.
- Hard-coded prompt object audit: no `CLASSIFICATION_PROMPT` or `DRAFT_RESPONSE_PROMPT` definitions remain.

## Regression Evidence

- Provider-capture tests prove custom classifier and drafter text reaches the provider.
- API validation tests reject missing and unsupported runtime variables.
- Success and failure tests prove the ledger hash matches the exact prompt bytes.
- API-to-graph integration proves an activated prompt produces the expected provider-prompt hash in the trace.

## Known Limits

- Historical AI runs have no rendered prompt hash because the exact provider input cannot be reconstructed reliably.
- V1 prompt syntax intentionally supports only `system:` and `human:` roles.
- The graph runner remains an oversized legacy module, but this ticket reduced it and did not add a new responsibility.

## Human Review

- Compare an active prompt version with the rendered hash shown in a new graph trace.
- Confirm invalid variables return `prompt_template_invalid` with HTTP 422.
- Confirm Alembic upgrades an existing database without requiring a historical backfill.

## Next Ticket

Implement transactional run-level token and cost reservations so every model call is checked against agent, per-run, workspace monthly, and model context limits before provider invocation.
