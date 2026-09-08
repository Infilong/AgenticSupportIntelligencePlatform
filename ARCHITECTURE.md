# Architecture and ownership

This is the top-level architecture contract. The [code map](docs/code-map.md) owns exact entry
points and current coupling; [quality score](docs/QUALITY_SCORE.md) owns verified status.
The [product spec](docs/product-spec.md) describes requirements, not completed capabilities.

## System flow
```text
React page → shell / feature state → HTTP client → FastAPI route
  → authenticated user + workspace permission → schema validation
  → domain service → SQLAlchemy / PostgreSQL → response → browser state

AgentService → LangGraph nodes → retrieval → context packing → model provider
  → confidence / guardrails → final answer or explicit human review
  → graph steps, retrieval traces, AI ledger, review and audit records
```

Compose runs the API, task worker, Vite frontend, PostgreSQL/pgvector and Redis. Durable
tasks use PostgreSQL admission records and execution ownership locks; Redis is not the task
queue. Interrupted active work fails explicitly rather than replaying actions. Historical
synchronous APIs remain readable; graph snapshots do not imply arbitrary durable resume.
An optional [built web image](infra/README.md#built-webapi-image) serves compiled assets and API
from one origin as a non-root process; the default Compose frontend remains development-only.
Model abstraction supports configured OpenAI-compatible calls and mocks. Embeddings default to
mock; opt-in OpenAI embeddings share configured indexing/query models and durable usage admission.

## Domains and owners
| Domain | Owns | Focused design |
| --- | --- | --- |
| Identity/workspaces | Authentication, membership and permission boundaries | [Security](docs/security-threat-model.md) |
| Multilingual data | Imports, examples, labels and EN/JA/ZH handling | [Database](docs/database-schema.md) |
| Knowledge/retrieval | Versions, chunks, ranking, citations and packed context | [RAG](docs/rag-design.md) |
| Agent workflow | Graph routing, tools and human-review transitions | [Graph](docs/langgraph-workflow-design.md), [tools](docs/tool-execution-design.md) |
| Quality/safety | Guardrails, evaluation cases and per-language metrics | [Evaluation](docs/evaluation-design.md) |
| Accounting/observability | AI runs, usage/cost, graph/retrieval traces and audit | [Tokens](docs/token-economy-design.md), [observability](docs/observability-design.md) |
| Browser | Rendering, draft state and explicit API error handling | [Frontend](frontend/README.md) |

## Dependency direction
UI rendering depends on feature state and API contracts, never database models. Routes compose
authentication, validation and services. Services depend on persistence and provider boundaries;
schemas/models must not import routers or UI. Backend owns transactions and authorization.
LangChain/LangGraph are implementation tools, not owners of permissions or accounting policy.
Current services still query/commit directly and some routers query models; a repository layer
is a refactoring destination, not a claim about the current tree.

## Invariants and forbidden shortcuts
Authenticate and authorize before workspace data enters retrieval/model/tool context. Scope
all owned resources and folder assignments to workspace_id. Persist attributable model, graph,
retrieval, review and cost records; see [reliability](docs/RELIABILITY.md) for failure contracts.
Do not bypass services with frontend authority, hide LLM calls inside unaccounted utilities,
use raw long documents as prompts, invent quality metrics, or call stored snapshots resumable.
No god components, catch-all utilities, unbounded resource lists or silent exception recovery.
Do not add queues, cloud infrastructure or scale claims merely to match an architecture diagram.

## Structural changes
Name each responsibility and allowed dependency before moving code. Preserve behavior with
boundary tests; extract one feature at a time. Apply [coding rules](codingRules.md), update the
code map and relevant local guide, and lower size baselines after shrinking legacy files.
Cross-cutting/security-sensitive changes need a [persistent plan](docs/PLANS.md) with migration,
rollback and compatibility decisions where applicable. Keep alternatives in plan Decisions or
[tradeoffs](docs/tradeoffs.md), not as conflicting implementation claims in multiple diagrams.
