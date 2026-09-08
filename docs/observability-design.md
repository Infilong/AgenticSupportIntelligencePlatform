# Observability Design

## HTTP outcome logs

`app/core/request_logging.py` emits one JSON outcome record per HTTP request with a generated
request ID, route template, method, status, elapsed milliseconds and exception type. Normal
and handled-error responses include `X-Request-ID`. `app/core/error_responses.py` handles
unexpected errors before a response starts with a no-store 500 JSON body:
`{"detail":{"code":"internal_error","message":"An internal error occurred.","request_id":"<UUID>"}}`.
The header and body use the same server-generated ID as the HTTP log; exception text is omitted.
Configured browser origins can read the header. The outer error handler reuses the configured
CORS origin policy because normal CORS middleware does not wrap this response.
The shared browser HTTP client displays UUID-shaped references for 5xx errors; 401 handling
and 4xx messages are unchanged. See [verification and limits](testing.md#client-visible-error-references).
Streaming failures may occur after a response status has been sent, when this handler cannot
replace it; inspect `error_type` as well as `status`.

Only route templates are logged: no raw path identifiers, query strings, credentials, body,
IP address or exception message. Unknown routes use `<unmatched>`. This applies to the new
application logger, not to every third-party/server logger. The container starts Uvicorn with
`--no-access-log` so its duplicate raw-path/query/IP access records do not bypass this contract.
`scripts/check_http_log_privacy.py` probes a synthetic unknown path/query and requires the
correlated structured outcome with no raw marker in captured server logs. The local runner
and browser CI job invoke it. Capture logs with
`docker compose -p asi-verification logs --timestamps api`.

## Server exception diagnostics
Container startup also loads `app/logging.json`. Its `app/core/server_logging.py` formatter
replaces exception-bearing Uvicorn log messages with a generic message and a `server_exception`
JSON diagnostic containing exception types and frame file basenames, function names and line
numbers. It omits exception text, message arguments, source lines, locals and stack text.
Output retains at most eight exceptions, including chained/grouped errors, and the last twenty
frames per exception. These diagnostics do not carry a request ID; the separate HTTP outcome
and client response share the request reference. Do not claim a direct exception-to-request join.

The saved [server logging tests](testing.md#server-exception-log-privacy) cover private markers
and a real Uvicorn 500 response. This configuration does not sanitize arbitrary third-party
loggers or sensitive text in ordinary non-exception messages. Full redaction and retention
remain release work; custom server launch commands must explicitly load this logging config.

## Evaluation failure diagnostics
Unexpected evaluation execution/publication failures emit `evaluation_execution_failed` with
evaluation_run_id, request_id (null outside HTTP), original error_type, failure_recorded and
recording_error_type. No exception message or case/model content is logged. A false
failure_recorded means storage could not persist the failed outcome; inspect the run before
taking recovery action. See [terminal failure tests](testing.md#evaluation-terminal-failures).

## Request-to-graph correlation
For HTTP-triggered graph execution, `asi.workflow` emits `graph_run_created` after the run
row is committed. Its only fields are event, server-generated request_id, graph_run_id and
trace_id. Join request_id to the HTTP outcome, then inspect the permission-gated graph trace
for retrieval/model records. System evaluations can emit multiple graph events under one
request ID. Failure after creation retains the link; denial before creation emits none.
Request context propagates into synchronous workers and resets on exit. Calls outside an
HTTP request do not fabricate a request ID or emit this event. This is not full distributed
tracing, background-worker propagation or correlation for graphless evaluations/embeddings.

## Graph-step ordering limitation
New graph steps carry a positive `sequence`, unique within their run. `graph_step_ordering.py`
locks the workspace-scoped run with PostgreSQL NO KEY UPDATE, allocates the next sequence and
selects its parent in the same transaction as step persistence. Trace, review-context and
latest-step readers use this order. It represents persistence order for the current serial
workflow, not a causal model for future parallel graph branches. Cross-run recency uses timestamps.

Legacy rows expose `sequence: null`; readers place them before sequenced rows using timestamp
and ID as a stable fallback. Their actual causal order and parent correctness remain unknown.
Appending to legacy history uses that best-effort last parent without rewriting old records.
The [repair plan](exec-plans/completed/graph-step-ordering.md) tracks migration/browser acceptance.
The original failed assertion and artifacts remain in [testing](testing.md#built-web-verification-harness).

## Goal
Retrieval traces now distinguish `succeeded`, `failed`, `pending` and historical `unknown`
outcomes. Direct post-validation embedding failures persist a trace and return its ID;
failed graph retrieval steps carry that ID. Permission-gated lookup is documented in
[API failure inspection](api-design.md). A successful empty search is not a provider failure.

Make AI workflow behavior inspectable. The system should show what happened, why it happened, which data was used, how much it cost, and whether quality passed.

## Required Records
- `GraphRun` for full workflow execution
- `GraphStep` for each LangGraph node
- `ToolCall` for tool execution
- `AIRun` for every model call
- `RetrievalTrace` and `RetrievedChunk` for retrieval
- `GuardrailResult` for guardrails
- `EvaluationRun`, `EvaluationResult`, and `EvaluationMetric` for evaluation
- `AuditLog` for workspace actions

## Intended navigation destinations
These are design destinations, not implemented URL routes. The current React shell uses
active-tab state; see the [frontend guide](../frontend/README.md).
```text
/login
/workspaces
/workspaces/{id}/datasets
/workspaces/{id}/documents
/workspaces/{id}/agent
/workspaces/{id}/agent-runs/{run_id}/trace
/workspaces/{id}/evaluations
/workspaces/{id}/costs
/workspaces/{id}/audit-logs
/settings
```

## Graph Run Trace Viewer
Show input message, detected language, intent classification, retrieved chunks, retrieval scores, selected citations, compressed context summary, draft response, policy/tone check, confidence score, routing decision, human-review status, final answer, model calls, token usage, estimated cost, latency, errors, and retries.

## Evaluation Dashboard
Show metrics by English, Japanese, and Chinese, with baseline comparisons and usage/cost.
The current metric contract reports citation presence and citation accuracy, not factual
groundedness. Historical grounding proxies remain identifiable. See [evaluation design](evaluation-design.md)
for implemented metric definitions and limitations; factual-support grading remains a target.

## Cost Dashboard
Show token usage, estimated cost, latency, model choice, cache hit rate, purpose, language, and trend summaries by workspace.


## Implemented In Milestone 6
- `AIRun` persistence for mock model calls.
- Workspace-scoped cost summary API.
- Token, estimated cost, latency, cache hit, status, and purpose tracking.
- Failed model calls are also recorded with error messages.
- Successful and failed calls store a SHA-256 hash of the exact rendered provider prompt.


## Implemented In Milestone 7
- `GraphRun`, `GraphStep`, and `ToolCall` persistence.
- Trace endpoint for graph runs.
- Graph steps can link to `AIRun` rows.
- Retrieval node links workflow execution to retrieval trace/tool-call evidence.

## Implemented In Milestone 9
- `EvaluationRun`, `EvaluationResult`, and `EvaluationMetric` persistence.
- Baseline comparison across `direct_llm`, `vector_rag`, and `system_v1`.
- Metrics are grouped by language and mode.
- Evaluation detail responses include per-case answers, citations, route decisions, prompt-token estimates, estimated cost, and errors.

## Implemented In Milestone 10
- Browser graph trace viewer for run, step, tool-call, token, cost, latency, retry, and error fields.
- Browser evaluation dashboard for per-language, per-mode metrics and case results.
- Browser cost dashboard for `AIRun` ledger aggregates and purpose breakdown.
- Browser human-review queue with approve/edit/reject resolution.


## Trace/span correlation

Each `GraphRun` owns a stable `trace_id`. Each persisted `GraphStep` owns a `span_id` and records the previous step as `parent_span_id` for the linear LangGraph execution path. The trace API exposes these identifiers so frontend debugging, logs, model calls, tool calls, guardrails, and future OpenTelemetry exports can be correlated without relying only on database primary keys.

## Trace response redaction

The graph trace API serializes through PublicTraceResponse and core/trace_redaction.py.
It masks recognized credential and sensitive structured keys, email addresses, bearer/key
patterns and credential assignments in free text. Nested JSON strings remain parseable;
model-copy updates are covered because redaction runs after final serialization. Explicit
private-chain-of-thought fields are omitted as redacted values. Numeric accounting, IDs,
citations and ordinary multilingual evidence remain intact.

This is a response boundary, not a storage rewrite: authorized task/review operations still
use their original persisted inputs. It does not provide encryption at rest, universal PII
detection, or a guarantee for unrecognized credential formats. Other resource endpoints
have separate data-access contracts. Do not put secrets into knowledge or agent instructions.
