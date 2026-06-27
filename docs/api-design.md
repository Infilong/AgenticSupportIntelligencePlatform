# API Design

## Principles
- All product APIs are versioned under `/api/v1`.
- Workspace-owned resources are nested under `/workspaces/{workspace_id}`.
- Protected routes require authentication.
- Workspace routes require membership.
- List endpoints are paginated.
- AI workflow APIs expose graph run IDs, trace IDs, token usage, and cost summaries where relevant.
- Errors are explicit and consistent.

## Auth
```text
POST /api/v1/auth/register
POST /api/v1/auth/login
```

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
GET  /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}
```

## Observability And Cost
```text
GET /api/v1/workspaces/{workspace_id}/costs/summary
GET /api/v1/workspaces/{workspace_id}/audit-logs
```

Current v1 behavior:
- returns aggregate `AIRun` counts, token totals, estimated cost, average latency, cache hit rate, and purpose breakdown.
- filters strictly by workspace membership and `workspace_id`.
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
