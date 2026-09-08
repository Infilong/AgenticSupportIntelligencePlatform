# API Design

## Input records
`GET /workspaces/{workspace_id}/records/{record_id}/attempts/{run_id}/review` requires
reviews:read and verifies record/execution/run workspace ownership. Returns the latest review
for that attempt, null when none exists, or 404 for an unmatched record/attempt. Resolution uses
the existing human-review endpoint and its unchanged authority and exact-action gates.

`GET /workspaces/{workspace_id}/records/{record_id}/attempts/{run_id}/artifacts` requires
traces:read. The record, execution, run and steps are workspace-scoped. Pagination uses offset
and limit (1–100, default 20). Artifacts identify saved step/run/time/status, expose selected
fields by step kind and redact response-only secrets/PII patterns. Private reasoning and arbitrary
state keys are omitted. Malformed saved JSON is reported explicitly; persisted evidence is unchanged.

`POST /workspaces/{workspace_id}/records/{record_id}/clarifications` requires `agents:run`.
Body: run_id, request_key, reply (nonblank, max 2000 characters). The run must belong to that
record/workspace and be awaiting_clarification. Creates a linked attempt and closes the waiting
question with route clarification_received, preserving its text and the original input. Replayed
matching submissions reuse the attempt; conflicting replies or a no-longer-waiting parent return
409. Reply text is user data, not corrected administrator instructions. Task run/history responses
include nullable clarification_reply. Migration 0039 preserves replies separately.

`GET /workspaces/{workspace_id}/records` requires `traces:read` and lists persisted task inputs,
not individual attempts. Parameters: literal `search` (max 200 chars), optional execution `status`,
`offset` (nonnegative), `limit` (1–100, default 20). The response includes items/total/offset/limit/
has_next. Each item has input identity/message/receipt time/creator, latest run/status, a result
summary bounded to 240 characters, and attempt count. Status filtering uses the latest attempt.
`GET /workspaces/{workspace_id}/records/{record_id}` returns the summary plus `input`, or 404.
`input` contains format (`text`/`json`), original content, caller-declared source
(`api`/`admin`/`cli`/`unknown`) and optional source_reference. Source is provenance supplied by
the caller, not authenticated identity; created_by_user_id always comes from authentication.
Legacy inputs have unknown source and preserve the stored text without fabricated provenance.
Both queries
scope input, execution and run to the workspace. Old run-only entries are not yet migrated into
this new view; existing run APIs remain available.

`POST /workspaces/{workspace_id}/records` requires `agents:run`; body contains agent_id,
request_key, input and optional language. Text must be nonblank; JSON must be a nonempty object
or array. Serialized processing content is bounded to 12,000 characters. Original whitespace
and JSON structure are retained in input_envelope_json; processing receives text or canonical
JSON. Metadata is not automatically promoted to model instructions. Extra fields are rejected.
Returns 202 with the saved record queued for the worker. Matching idempotency keys reuse the
input; a changed payload/source with the same key returns 409. Retries cannot replace the original.
Migration 0038 adds nullable input storage; downgrade refuses to discard populated originals.

## Recover orphaned embedding attempts
`POST /workspaces/{workspace_id}/embedding-attempts/{attempt_id}/recover` requires
`budget_policy:manage` and a nonblank `reason` of at most 240 characters. New attempt responses
include nullable execution ID/protocol. Recovery requires `pg-session-v1` and PostgreSQL,
acquires ownership without waiting, then rechecks membership, workspace and attempt state.
It atomically records an audit and changes pending to uncertain, retaining usage estimates.
Live ownership, unsupported provenance and nonpending attempts return explicit 409 codes;
foreign attempts are 404 and denied roles are 403. Billing reconciliation stays separate.
See the [operator protocol](design-docs/interrupted-execution-ownership.md#operator-api).

## Evaluation comparison compatibility
New evaluation score JSON carries `evaluation_contract`. Comparison rows return
`direction: incomparable` and `delta: null` when either mode/language group lacks the current
known matching contract or identical loaded-case fingerprint multiset, while retaining
current/baseline values. Scores preserve `evaluation_case_fingerprint`; case reordering is
allowed but changed inputs, expectations or duplicate counts are incomparable. These rows do not count as
improvements or regressions. See [contract provenance](evaluation-design.md#comparison-contract-provenance).

## Evaluation expectation metrics
New evaluation results add expected tool/guardrail lists to `scores_json`; corresponding match
scores are null when untested. New metric keys are `expected_tool_call_match_rate` and
`expected_guardrail_detection_rate`. For new runs, missing keys mean no evaluated cases for
that behavior, not zero or perfect performance. Older runs lack rates under the corrected
method; historical metric rows retain their old names and values.
Clients must not equate the old all-case rates with these expectation-only rates; see the
[scoring contract](evaluation-design.md#optional-expectation-metrics).

## Running evaluation deletion
`DELETE /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}/permanent` returns
409 with `detail.code = evaluation_running` when an archived evaluation is still running,
even between model calls with no active reservation. The existing `evaluation_reservation_active`
conflict takes precedence when a reservation is active. Authorization and archive prerequisites
are unchanged. A terminal archived evaluation remains deletable; archive alone does not cancel
execution. Stale running records require a future explicit recovery workflow, not forced deletion.
See [verification](testing.md#running-evaluation-deletion-protection).

## Imported message language
CSV headers must be unique, and rows must not contain more fields than their header. Violations
return `dataset_import_failed` with a structural error instead of echoing conversation content.
CSV parsing uses the standard library's strict dialect handling: unterminated quoted fields
and unexpected characters after a closing quote return a typed import error with a line hint,
without echoing source text. Quoted commas, newlines and doubled-quote escapes remain valid.
This is the supported parser dialect, not a claim to validate every possible CSV convention.

JSONL message `content` must be a nonempty string; objects, arrays, numbers, booleans and null
are rejected rather than converted to text. Errors identify line/message position without
echoing the value. Numeric text such as `"123"` remains valid with a declared language or a
language-bearing message in the same conversation.

JSONL accepts an optional `language` on each conversation; CSV accepts an optional `language`
column. Values are `en`, `ja` or `zh`. A declared language annotates the conversation and all
its messages, allowing kanji-only Japanese or numeric conversations without heuristic guessing.
Omission, JSON null or an empty field uses automatic detection. Invalid/non-string values
return a typed import error before any examples are written. This metadata neither translates
text nor verifies that content matches the declared language. For mixed-language conversations,
omit the declaration to retain per-message detection.

```json
{"language":"ja","messages":[{"role":"user","content":"返金申請"}]}
```

```csv
role,content,language
user,返金申請,ja
```

With automatic detection:
Dataset JSONL conversations may contain numeric, punctuation-only or emoji replies. Nonempty
messages without letters inherit the language detected from their own conversation; original
content is preserved. Alphabetic messages still pass through language detection independently.
A conversation without a declaration or supported-language signal remains invalid, even if another conversation
in the batch has a language. CSV rows are separate conversations and do not inherit from other
rows. Unsupported alphabetic scripts remain explicit validation errors; all languages are
validated before examples are written. Detection remains heuristic for kanji-only/mixed text.

## Support run language
`POST /api/v1/workspaces/{workspace_id}/agents/{agent_id}/runs` accepts
`{"input_message":"返金申請","language":"ja"}`. Language is optional: `en`, `ja`, `zh`,
or null; omission/null preserves automatic detection. Invalid values return 422 before run
creation. Existing workspace permission, active-agent and budget admission checks still apply.
The selected language controls retrieval/model context and `GraphRun.language`; the
`detect_language` step records `language_source` as `requested` or `detected`. Its legacy
`detected_language` state key contains the selected value even when explicitly requested.
Selection does not translate evidence or disable language/safety guardrails. Automatic
detection remains heuristic, particularly for kanji-only Japanese and mixed-language text.

## Principles
Folder PATCH distinguishes omission from null: `{"name":"Policies"}` preserves the existing
parent; `{"parent_folder_id":null}` explicitly moves the folder to root. A supplied parent
must belong to the same workspace and resource type. Invalid parent changes are rejected
before the name or hierarchy is persisted. Browser rename submits only the name.
Moving a folder beneath itself or a descendant returns 400 (`resource_folder_invalid`).
Parent updates are serialized per workspace and validate ancestry before persistence;
existing corrupt trees are not automatically rewritten.
Folder create/update/delete commit their audit record with the folder change. Audit persistence
failure rolls back the mutation; a corrected retry does not duplicate the earlier failed action.

- All product APIs are versioned under `/api/v1`.
- Workspace-owned resources are nested under `/workspaces/{workspace_id}`.
- Protected routes require authentication.
- Workspace routes require membership.
- List endpoints are paginated.
- AI workflow APIs expose graph run IDs, trace IDs, token usage, and cost summaries where relevant.
- Errors are explicit and consistent.

## Retrieval failure inspection
After language validation and trace creation, embedding transport/response/vector failures return
HTTP 400 with `detail.code = retrieval_failed` and `detail.trace_id`. The direct route commits
the failed trace before returning that ID. Database failure is not disguised as a saved trace;
validation before trace creation can return a null ID. Graph callers own their transaction and
retain the trace ID in failed retrieval-step output.

`GET /api/v1/workspaces/{workspace_id}/retrieval/traces/{trace_id}` requires `knowledge:read`,
scopes records to the workspace and returns 404 for foreign/missing IDs. It exposes query,
filters, latency, `no_source`, `outcome` and a stable `error_code`. Queries are protected content,
not general log material. `failed` with `embedding_failed` differs from a successful empty search;
historical outcomes are `unknown`.

## Auth
```text
POST /api/v1/auth/register
POST /api/v1/auth/login
```

## Embedding usage reconciliation
`GET /api/v1/workspaces/{workspace_id}/embedding-attempts` requires `costs:read` and returns
unresolved pending/uncertain OpenAI embedding attempts in creation-time/ID order. `limit` is
1–100 (default 20), `offset` is nonnegative; response contains `items` and `has_more`.
Pagination is bounded, not a snapshot across concurrent updates.

`POST /api/v1/workspaces/{workspace_id}/embedding-attempts/{attempt_id}/reconcile` requires
owner-only `budget_policy:manage` and an unarchived workspace. Body:
```json
{"confirmed_tokens": 7, "evidence_reference": "billing-investigation-17"}
```
Use an internal billing evidence identifier, not customer text or credentials. Confirmed tokens
must be an integer from zero through 2,147,483,647; zero means verified no usage. The reference
is required and bounded to 240 characters. The server does not fetch or validate that external
evidence. Supply confirmed usage only after investigating provider billing.

Only `uncertain` embedding attempts can change. Pending, succeeded and already reconciled rows
return 409; foreign or nonembedding IDs return 404. Validation failures return 422. The service
locks workspace then attempt, preserves admission-time pricing, and commits updated usage with
actor/reference/before-and-after audit evidence atomically. Failure rolls back both writes.
The result is `failed` with `embedding_failed_usage_reconciled`: billing confirmation does not
recover vectors, rerun the provider or retroactively change graph outcomes. The Usage & costs
panel exposes owner confirmation and read-only inspection. Safe pending-attempt crash recovery
is not implemented yet.

## Workspaces
```text
GET  /api/v1/workspaces
POST /api/v1/workspaces
GET  /api/v1/workspaces/{workspace_id}
```

## Datasets
```text
POST /api/v1/workspaces/{workspace_id}/datasets/import
GET  /api/v1/workspaces/{workspace_id}/datasets
GET  /api/v1/workspaces/{workspace_id}/datasets/{dataset_id}/examples
POST /api/v1/workspaces/{workspace_id}/examples/{example_id}/labels
```

## Knowledge Documents
```text
POST /api/v1/workspaces/{workspace_id}/knowledge-documents
GET  /api/v1/workspaces/{workspace_id}/knowledge-documents
GET  /api/v1/workspaces/{workspace_id}/knowledge-documents/{document_id}
POST /api/v1/workspaces/{workspace_id}/knowledge-documents/{document_id}/reindex
```



Current v1 upload payload:
```json
{
  "title": "Refund Policy JA",
  "content_type": "text/markdown",
  "content": "# Refund policy...",
  "language": "ja"
}
```

Current v1 behavior:
- accepts plain text and markdown content payloads.
- rejects unsupported file types such as PDF/DOCX until parsers are added.
- indexes synchronously through `KnowledgeService` for local v1, behind a service boundary that can move to Redis workers later.
- creates document version, chunks, and mock embeddings during upload/reindex.

## Retrieval
```text
POST /api/v1/workspaces/{workspace_id}/retrieval/search
```

Retrieval must filter by workspace and return citation metadata. Retrieval calls should create `RetrievalTrace` rows.


Current v1 retrieval payload:
```json
{
  "query": "返金は何日以内ですか？",
  "language": "ja",
  "top_k": 5,
  "min_score": 0.2,
  "document_id": null
}
```

Current v1 behavior:
- filters candidates by workspace before scoring.
- supports optional language and document filters.
- combines mock vector similarity with multilingual lexical scoring.
- uses character n-gram lexical matching for Japanese and Chinese.
- stores `RetrievalTrace` and `RetrievedChunk` rows for every search.
- returns `no_source=true` with an empty result list when evidence is too weak.

## Agent Runs
```text
POST /api/v1/workspaces/{workspace_id}/agents
GET  /api/v1/workspaces/{workspace_id}/agents
POST /api/v1/workspaces/{workspace_id}/agents/{agent_id}/runs
GET  /api/v1/workspaces/{workspace_id}/agent-runs/{run_id}
GET  /api/v1/workspaces/{workspace_id}/agent-runs/{run_id}/trace
POST /api/v1/workspaces/{workspace_id}/agent-runs/{run_id}/review

GET  /api/v1/workspaces/{workspace_id}/human-reviews
GET  /api/v1/workspaces/{workspace_id}/human-reviews/{review_id}
POST /api/v1/workspaces/{workspace_id}/human-reviews/{review_id}/resolve
```

Current v1 behavior:
- agents can be created/listed per workspace.
- agent runs execute the LangGraph support workflow synchronously for local v1.
- run and trace endpoints are workspace-scoped.
- trace responses include ordered graph steps, tool calls, linked AI run IDs, token/cost fields where present, and final route decision.


## Evaluations
```text
POST /api/v1/workspaces/{workspace_id}/evaluations
GET  /api/v1/workspaces/{workspace_id}/evaluations
GET  /api/v1/workspaces/{workspace_id}/evaluations?include_archived=true
GET  /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}
DELETE /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}
```

Current v1 payload:
```json
{
  "name": "Smoke evaluation",
  "jsonl_cases": "{...}\\n{...}",
  "modes": ["direct_llm", "vector_rag", "system_v1"],
  "agent_id": null
}
```

Current v1 behavior:
- stores uploaded JSONL cases as workspace-scoped `EvaluationCase` rows.
- runs selected modes synchronously for local v1.
- stores one `EvaluationResult` per case and mode.
- stores aggregate `EvaluationMetric` rows by mode and language.
- archives evaluation runs through an owner-only soft-delete endpoint that preserves results and metrics.
- hides archived runs by default; `include_archived=true` returns them for audit and comparison history.
- enforces workspace membership on create, list, and detail routes and workspace ownership on archive.
- uses mock providers in tests; no test calls a real model provider.


## Prompt Templates And Model Configs
```text
GET    /api/v1/workspaces/{workspace_id}/prompt-templates
GET    /api/v1/workspaces/{workspace_id}/prompt-templates?include_archived=true
POST   /api/v1/workspaces/{workspace_id}/prompt-templates
POST   /api/v1/workspaces/{workspace_id}/prompt-templates/{template_id}/activate
DELETE /api/v1/workspaces/{workspace_id}/prompt-templates/{template_id}

GET    /api/v1/workspaces/{workspace_id}/model-configs
GET    /api/v1/workspaces/{workspace_id}/model-configs?include_archived=true
POST   /api/v1/workspaces/{workspace_id}/model-configs
POST   /api/v1/workspaces/{workspace_id}/model-configs/{model_config_id}/activate
DELETE /api/v1/workspaces/{workspace_id}/model-configs/{model_config_id}
```

Current v1 behavior:
- list routes require workspace membership and hide archived records by default.
- create, activate, and archive routes require workspace owner access.
- archive is a soft delete through `archived_at`; archived records remain available with `include_archived=true`.
- archived prompt templates and model configs are excluded from active runtime lookup.
- archiving a model config clears agent-level model assignments that referenced it.

## Observability, Budget Policy, And Cost
```text
GET /api/v1/workspaces/{workspace_id}/budget-policy
PUT /api/v1/workspaces/{workspace_id}/budget-policy
GET /api/v1/workspaces/{workspace_id}/costs/summary
GET /api/v1/workspaces/{workspace_id}/audit-logs
```

Current v1 behavior:
- returns aggregate `AIRun` counts, token totals, estimated cost, average latency, cache hit rate, and purpose breakdown.
- returns monthly token/cost usage against the workspace budget policy.
- lets workspace owners update monthly budgets, per-run caps, hourly run limit, and alert threshold.
- filters strictly by workspace membership and `workspace_id`; budget policy updates require workspace owner access.
- returns estimates only; pricing is demo/provider-config based and not billing-grade.


## Serving
```text
POST /api/v1/workspaces/{workspace_id}/serving/chat
```

Serving responses must include answer or review/refusal status, language, citations, graph run ID, token usage summary, and estimated cost.

## Error Shape
```json
{
  "error": {
    "code": "workspace_forbidden",
    "message": "You do not have access to this workspace.",
    "details": {}
  }
}
```

## API Review Checklist
Verify authentication, workspace membership, `workspace_id` filtering, pagination, explicit errors, traceability, and token/cost exposure.


Human review v1 supports pending review listing/detail and approve/edit/reject resolution. Guardrail and review data are workspace-scoped.

### Retrieval and workspace archive
New `POST /workspaces/{workspace_id}/retrieval/search` requires knowledge:read and an active
workspace. Even owners receive 409/workspace_archived before retrieval/provider execution when
the workspace is archived: a search can incur embedding usage and persist traces, so it is not
an archival read. `GET /workspaces/{workspace_id}/retrieval/traces/{trace_id}` remains available
to authorized readers of archived workspaces. Restoring a workspace re-enables search under the
same role permissions. The archive check governs new request admission; it does not cancel a
request already admitted before a concurrent archive.
## Saved knowledge versions

`GET /api/v1/workspaces/{workspace_id}/knowledge-documents/{document_id}/versions/{version}`
requires `knowledge:read` and returns the stored version, including original text and creation
time. Version numbers must be positive. Document and version must both belong to the authorized
workspace. Missing/deleted versions and foreign resources return 404; unauthenticated calls
return 401. This read does not reindex, call a model, or substitute the latest version.
