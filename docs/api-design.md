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

## Retrieval
```text
POST /api/v1/workspaces/{workspace_id}/retrieval/search
```

Retrieval must filter by workspace and return citation metadata. Retrieval calls should create `RetrievalTrace` rows.

## Agent Runs
```text
POST /api/v1/workspaces/{workspace_id}/agents/{agent_id}/runs
GET  /api/v1/workspaces/{workspace_id}/agent-runs/{run_id}
GET  /api/v1/workspaces/{workspace_id}/agent-runs/{run_id}/trace
POST /api/v1/workspaces/{workspace_id}/agent-runs/{run_id}/review
```

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
