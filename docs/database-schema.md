# Database Schema Draft

This is the starting database model. Exact SQLAlchemy models and Alembic migrations will be created during implementation milestones.

## Global Rules
- Every workspace-owned entity must include `workspace_id`.
- Workspace-scoped queries must filter by `workspace_id`.
- Language fields use `en`, `ja`, or `zh` in v1.
- Store timestamps in UTC.
- Do not log PII, raw secrets, or raw long documents by default.

## Auth And Workspace
```text
User
- id
- email
- password_hash
- display_name
- created_at

Workspace
- id
- name
- created_by_user_id
- created_at

WorkspaceMember
- id
- workspace_id
- user_id
- role
- created_at

AuditLog
- id
- workspace_id
- actor_user_id nullable
- action
- resource_type
- resource_id
- metadata_json
- created_at
```

## Dataset Curation
```text
Dataset
- id
- workspace_id
- name
- description
- created_at

ImportBatch
- id
- workspace_id
- dataset_id
- source_type
- status
- error_message nullable
- created_at

ConversationExample
- id
- workspace_id
- dataset_id
- import_batch_id nullable
- external_id nullable
- language
- status
- created_at

Message
- id
- workspace_id
- conversation_example_id
- role
- language
- content
- created_at

Label
- id
- workspace_id
- conversation_example_id
- label_type
- value
- source
- created_by_user_id nullable
- created_at

LanguageConfig
- id
- workspace_id nullable
- language
- chunking_strategy
- tone_rules_json
- evaluation_rubric_json
- active
```

## Knowledge And Retrieval
```text
KnowledgeDocument
- id
- workspace_id
- title
- language
- status: pending / indexing / indexed / failed
- error_message nullable
- created_by_user_id
- created_at
- updated_at

DocumentVersion
- id
- workspace_id
- knowledge_document_id
- version
- content_hash
- content_type
- raw_text
- created_at

DocumentChunk
- id
- workspace_id
- document_version_id
- language
- chunk_index
- content
- token_count
- chunk_metadata
- created_at

Embedding
- id
- workspace_id
- document_chunk_id
- provider
- model
- vector: pgvector vector(16) for local mock provider in v1
- created_at

RetrievalTrace
- id
- workspace_id
- graph_run_id nullable
- query
- language
- strategy
- filters_json
- latency_ms
- no_source
- created_at

RetrievedChunk
- id
- workspace_id
- retrieval_trace_id
- document_chunk_id
- rank
- vector_score nullable
- lexical_score nullable
- combined_score
- citation
```

## Agent Workflow
```text
AgentConfig
- id
- workspace_id
- name
- active
- model_config_id
- token_budget
- settings_json
- created_at

GraphRun
- id
- workspace_id
- agent_config_id
- user_id
- input_message
- language
- status
- route_decision nullable
- final_answer nullable
- created_at
- completed_at nullable

GraphStep
- id
- workspace_id
- graph_run_id
- step_name
- input_json
- output_json
- status
- latency_ms
- ai_run_id nullable
- token_count nullable
- estimated_cost nullable
- error_message nullable
- retry_count
- created_at

ToolCall
- id
- workspace_id
- graph_run_id
- graph_step_id
- tool_name
- input_json
- output_json
- status
- latency_ms
- created_at

HumanReview
- id
- workspace_id
- graph_run_id
- reviewer_id nullable
- reason
- proposed_answer
- reviewer_decision: pending / approved / edited / rejected
- edited_answer nullable
- comments nullable
- created_at
- resolved_at nullable

Checkpoint
- id
- workspace_id
- graph_run_id
- checkpoint_key
- state_json
- created_at
```

## Guardrails And Safety
```text
GuardrailResult
- id
- workspace_id
- graph_run_id
- graph_step_id nullable
- guardrail_type
- passed
- severity
- message
- created_at
```

Every guardrail should log a result.

## AI Observability
```text
ModelConfig
- id
- workspace_id nullable
- provider
- model
- purpose
- input_cost_per_1k
- output_cost_per_1k
- active

PromptTemplate
- id
- workspace_id
- name
- language
- version
- template_text
- active
- created_at

AIRun
- id
- workspace_id
- graph_run_id nullable
- graph_step_id nullable
- provider
- model
- purpose
- language
- prompt_template_id nullable
- prompt_version nullable
- prompt_tokens
- completion_tokens
- total_tokens
- estimated_cost
- latency_ms
- cache_hit
- status
- error_message nullable
- created_at

CacheEntry
- id
- workspace_id
- cache_key
- cache_type
- value_json
- expires_at nullable
- created_at
```

Every model call should create an `AIRun`. Every AI run should record prompt template and version when a prompt template is used.

## Evaluation
```text
EvaluationCase
- id
- workspace_id
- external_id
- language
- input_message
- expected_intent nullable
- expected_product_area nullable
- expected_sources_json
- must_include_json
- must_not_include_json
- expected_route
- safety_risk
- max_prompt_tokens nullable
- metadata_json
- created_at

EvaluationRun
- id
- workspace_id
- name
- modes_json
- status: running / completed / failed
- total_cases
- created_by_user_id
- created_at
- completed_at nullable
- archived_at nullable

EvaluationResult
- id
- workspace_id
- evaluation_run_id
- evaluation_case_id
- mode: direct_llm / vector_rag / system_v1
- language
- actual_route
- answer nullable
- citations_json
- passed
- scores_json
- latency_ms
- prompt_tokens
- estimated_cost
- error_message nullable
- created_at

EvaluationMetric
- id
- workspace_id
- evaluation_run_id
- mode
- language
- metric_name
- metric_value
- created_at
```

Evaluation data is workspace-owned. Results and metrics must always be queried through the parent workspace and run IDs, never by global IDs alone.

## Required Permission Tests
Add permission tests for documents, datasets, examples, labels, graph runs, human reviews, evaluations, cost summaries, and audit logs.
