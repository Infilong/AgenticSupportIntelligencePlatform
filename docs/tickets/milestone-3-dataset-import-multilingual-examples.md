# Milestone 3: Dataset Import And Multilingual Examples

## Goal
Build the multilingual dataset curation foundation: workspace-scoped datasets, import batches, conversation examples, messages, manual labels, deterministic language detection for English/Japanese/Chinese, and CSV/JSONL import.

The goal is to make real multilingual support data inspectable and editable before adding knowledge documents, RAG, LangGraph workflows, or model calls.

## Context
Relevant docs:
- `AGENTS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/architecture-tree.md`
- `docs/database-schema.md`
- `docs/api-design.md`
- `docs/security-threat-model.md`
- `docs/milestone-plan.md`

Already implemented:
- FastAPI app and `/health`
- SQLAlchemy and Alembic
- PostgreSQL/pgvector through Docker Compose
- JWT auth
- workspace membership dependency
- `User`, `Workspace`, and `WorkspaceMember`
- permission tests for workspace isolation

This milestone starts Pillar 1: Multilingual Data Platform.

## Requirements
- Add SQLAlchemy models and Alembic migration for:
  - `Dataset`
  - `ImportBatch`
  - `ConversationExample`
  - `Message`
  - `Label`
- Every new table must include `workspace_id`.
- Add deterministic language detection for v1 languages: `en`, `ja`, `zh`.
- Add import support for JSONL and CSV payloads.
- Store import batch status and errors.
- Store detected language on conversation examples and messages.
- Add manual label editing API.
- Add workspace-scoped dataset/example APIs:
  - `POST /api/v1/workspaces/{workspace_id}/datasets/import`
  - `GET /api/v1/workspaces/{workspace_id}/datasets`
  - `GET /api/v1/workspaces/{workspace_id}/datasets/{dataset_id}/examples`
  - `POST /api/v1/workspaces/{workspace_id}/examples/{example_id}/labels`
- Use the existing workspace membership dependency for every route.
- Add seed/demo data files for English, Japanese, and Chinese examples.
- Add tests for import, language detection, labels, and cross-workspace denial.

## Non-goals
- No document ingestion or embeddings.
- No RAG, retrieval, citations, or pgvector writes.
- No LangChain or LangGraph use.
- No LLM-based classification or labeling.
- No frontend dataset UI yet.
- No async worker yet; imports can be synchronous in this milestone.
- No complex CSV auto-mapping UI.
- No evaluation runner yet.
- No PII redaction yet, but do not add logging that prints imported message contents.

## Design Plan
Backend structure:

```text
backend/app/
  api/v1/datasets.py
  core/language.py
  models/dataset.py
  schemas/dataset.py
  services/dataset_service.py
  services/import_parser.py
backend/alembic/versions/0002_dataset_curation.py
backend/tests/test_datasets.py
backend/demo_data/conversations/*.jsonl
```

Model sketch:

```text
Dataset
- id
- workspace_id
- name
- description nullable
- created_at

ImportBatch
- id
- workspace_id
- dataset_id
- source_type: jsonl / csv
- status: completed / failed
- error_message nullable
- created_at

ConversationExample
- id
- workspace_id
- dataset_id
- import_batch_id nullable
- external_id nullable
- language: en / ja / zh
- status
- created_at

Message
- id
- workspace_id
- conversation_example_id
- role: user / assistant / system
- language: en / ja / zh
- content
- created_at

Label
- id
- workspace_id
- conversation_example_id
- label_type
- value
- source: human / import
- created_by_user_id nullable
- created_at
```

Language detection:
- Use deterministic Unicode/script heuristics, not an LLM.
- If text contains Japanese kana, classify as `ja`.
- If text contains CJK ideographs and no kana, classify as `zh` for v1.
- Otherwise classify as `en` when Latin text is dominant.
- Reject or mark unsupported language only if the input has no meaningful text.
- Document limitations: Japanese kanji-only text can be ambiguous and will be detected as `zh` until a better detector is introduced.

Import payload format:
- Accept a request body with `dataset_name`, optional `description`, `source_type`, and `content` string.
- For JSONL, each line should represent one conversation example.
- For CSV, require predictable columns rather than fuzzy inference.

JSONL example:
```json
{"external_id":"ja_refund_001","messages":[{"role":"user","content":"返金できますか？"}],"labels":{"intent":"refund_request"}}
```

CSV columns:
```text
external_id,role,content,label_intent,label_product_area,label_escalation_needed
```

For v1 CSV, one row can become one single-message conversation example. Multi-row grouped conversations can be postponed unless implementation remains simple.

Label behavior:
- Import can create labels with `source=import`.
- Manual label endpoint creates or replaces a label for the example, label type, and current user with `source=human`.
- Validate supported label types initially with a conservative enum/list:
  - `intent`
  - `sentiment`
  - `product_area`
  - `escalation_needed`
  - `safety_risk`
  - `response_quality`

Permission behavior:
- Dataset list returns only datasets in the workspace.
- Example list requires the dataset to belong to the route workspace.
- Label editing requires the example to belong to the route workspace.
- Cross-workspace dataset/example IDs must not leak data.

## Files Likely To Change
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/datasets.py`
- `backend/app/core/language.py`
- `backend/app/models/__init__.py`
- `backend/app/models/dataset.py`
- `backend/app/schemas/dataset.py`
- `backend/app/services/dataset_service.py`
- `backend/app/services/import_parser.py`
- `backend/alembic/versions/0002_dataset_curation.py`
- `backend/tests/test_datasets.py`
- `backend/demo_data/conversations/*.jsonl`
- `docs/learning/milestone-3-dataset-import.md`
- Possibly `README.md` if demo/import commands are added

## Database Migrations
Create `0002_dataset_curation` with:
- `datasets`
- `import_batches`
- `conversation_examples`
- `messages`
- `labels`

Required indexes/constraints:
- indexes on each `workspace_id`
- foreign keys with cascade behavior where appropriate
- index for `conversation_examples(dataset_id)`
- index for `messages(conversation_example_id)`
- index or unique constraint for label replacement, likely `(workspace_id, conversation_example_id, label_type, source)` if replacement semantics are simple

Do not add knowledge document, embedding, graph, AI run, or evaluation tables yet.

## API Changes
### `POST /api/v1/workspaces/{workspace_id}/datasets/import`
Protected. Requires workspace membership.

Request:
```json
{
  "dataset_name": "Support examples",
  "description": "Optional description",
  "source_type": "jsonl",
  "content": "{...}\n{...}"
}
```

Response:
```json
{
  "dataset": {"id": "...", "name": "Support examples"},
  "import_batch": {"id": "...", "status": "completed"},
  "imported_examples": 3
}
```

### `GET /api/v1/workspaces/{workspace_id}/datasets`
Protected. Returns datasets for the workspace.

### `GET /api/v1/workspaces/{workspace_id}/datasets/{dataset_id}/examples`
Protected. Returns examples, messages, and labels for a dataset in the workspace.

### `POST /api/v1/workspaces/{workspace_id}/examples/{example_id}/labels`
Protected. Creates or replaces a human label on an example in the workspace.

Request:
```json
{
  "label_type": "intent",
  "value": "refund_request"
}
```

## Test Plan
Unit tests:
- language detection for English.
- language detection for Japanese kana.
- language detection for Chinese CJK text.
- JSONL parser rejects invalid lines clearly.
- CSV parser handles required columns.
- label type validation rejects unsupported label types.

API/integration tests:
- authenticated user imports JSONL examples.
- import stores dataset, import batch, examples, messages, languages, and import labels.
- authenticated user imports CSV examples.
- dataset list is workspace-scoped.
- example list is workspace-scoped.
- manual label editing works.
- user cannot list/read/label another workspace's examples.
- unauthenticated requests are rejected.

Migration/runtime checks:
- Alembic migration applies with `make backend-migrate`.
- Existing auth/workspace tests still pass.
- Docker Compose still starts.

Validation commands:
```bash
make backend-lint
make backend-test
make frontend-test
make backend-migrate
docker compose up --build -d
curl http://127.0.0.1:8000/health
docker compose down
```

## Acceptance Criteria
- Multilingual examples can be imported from JSONL.
- CSV import works for the documented v1 format.
- Language is stored on examples and messages.
- Labels can be imported and manually edited.
- Dataset/example/label APIs enforce workspace membership.
- Cross-workspace access is tested and denied.
- No LLM calls or AI provider dependencies are introduced.
- Tests cover parsing, language detection, labels, and permissions.
- Learning note is added.

## Risks
- Permission leak: dataset ID from another workspace could be used under the current route workspace.
- Ambiguous language detection: Japanese kanji-only text may be misclassified as Chinese.
- Parser overreach: trying to support every CSV format would expand scope too early.
- PII risk: imported message content should not be printed in errors or logs.
- Fake implementation risk: language detection must be deterministic and tested, not a placeholder returning `en`.
- Scope creep: auto-labeling with LLMs belongs later, after AI run ledger and token tracking exist.

## Human Review Checklist
- Confirm every new model has `workspace_id`.
- Confirm every route uses workspace membership checks.
- Confirm queries filter by both route `workspace_id` and resource IDs.
- Confirm tests include cross-workspace denial for examples and labels.
- Confirm no LLM/LangChain/LangGraph code was added early.
- Confirm import error messages are useful but do not dump full message content.
- Confirm language detection limitations are documented in the learning note.

## Operating Notes
After implementation:
- Add `docs/learning/milestone-3-dataset-import.md`.
- Self-review specifically for workspace leaks and fake language detection.
- Be able to explain why deterministic language detection and human labels come before LLM-powered classification.
