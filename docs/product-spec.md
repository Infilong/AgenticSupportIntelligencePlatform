# Product Spec

## Project Name
Multilingual Agentic Support Intelligence Platform

## Subtitle
A multilingual AI support platform for dataset curation, RAG, LangGraph workflows, human review, evaluation, and token/cost observability.

## Primary Goal
Build a production-style AI/backend platform that demonstrates backend architecture, multilingual AI systems, dataset curation, RAG quality, LangChain, LangGraph workflow orchestration, human review, guardrails, evaluation, token economy, observability, auditability, permission isolation, Docker-based local deployment, clean documentation, and production-defensible engineering decisions.

This must not look like a tutorial chatbot or junior portfolio project. It should look like a small but serious internal AI platform that a SaaS company could use for multilingual support, product, and community workflows.

## Target Roles
- Backend Engineer with AI product experience
- AI Application Engineer
- Python Backend Engineer
- Product Engineer for AI-enabled SaaS
- Mid-to-senior AI Platform Engineer
- RAG / LLM Application Engineer
- Agent workflow / LangGraph engineer

## Core Product Narrative
A SaaS company receives support, community, and product feedback in English, Japanese, and Chinese.

The internal team needs to:
1. Import multilingual customer conversations.
2. Detect language automatically.
3. Label examples by intent, sentiment, product area, escalation need, safety risk, and response quality.
4. Upload product docs, policies, FAQs, release notes, and support manuals.
5. Run a LangGraph-based support agent over new customer messages.
6. Retrieve relevant evidence with citations.
7. Generate same-language responses.
8. Route risky, low-confidence, unsupported, or high-cost cases to human review.
9. Evaluate output quality separately for English, Japanese, and Chinese.
10. Monitor token usage, cost, latency, model choice, cache hit rate, and quality metrics.
11. Inspect every workflow step through a graph trace viewer.

Portfolio story:

> I built a multilingual AI support intelligence platform. It imports and labels English/Japanese/Chinese conversations, indexes knowledge documents, runs a LangGraph support-agent workflow with RAG and human review, evaluates outputs per language, and tracks every model call for cost, latency, cache usage, and quality. The system is local-first but designed with clean backend boundaries, workspace isolation, async workers, pgvector retrieval, audit logs, and a documented cloud-scale migration path.

## Phase 1: Production-Grade Vertical Slice
Phase 1 must include:
1. FastAPI backend
2. PostgreSQL + pgvector
3. Redis async worker
4. Docker Compose
5. User auth
6. Workspace isolation
7. Multilingual conversation import
8. Language detection for English, Japanese, and Chinese
9. Manual label editing
10. Knowledge document upload
11. Background document chunking and embedding
12. LangGraph support-agent workflow
13. RAG retrieval with citations
14. Same-language response generation
15. No-source refusal
16. Token-budget enforcement
17. Human-review routing
18. Graph run trace storage
19. AI run ledger for model calls
20. Evaluation runner with JSONL cases
21. Evaluation dashboard by language
22. Cost/token dashboard
23. pytest test suite
24. GitHub Actions CI
25. README and architecture docs

Detailed sequencing lives in `docs/milestone-plan.md`.

## Phase 2 Extensions
Add only after Phase 1 is stable:
1. Retrieval reranking
2. Better context compression
3. Prompt template/version management
4. Response caching
5. More evaluation cases
6. PII detection/redaction
7. More detailed audit logs
8. Baseline comparison report
9. Admin debug views
10. Cloud deployment design document
11. Optional GCP Cloud Run deployment

## Postponed Features
Do not implement in v1:
- Kubernetes
- Terraform
- BigQuery
- dedicated external vector database
- arbitrary language plugin system
- full enterprise SSO
- complex role hierarchy
- multimodal documents
- fine-tuning
- real email/task external integrations
- multi-region scale
- complex frontend design

The project should document the scale path, but not pretend to implement million-record infrastructure in v1.

## Success Criteria
- The project can be understood as a serious internal AI platform, not a tutorial chatbot.
- The demo path works from data import through evaluation and cost inspection.
- Workspace isolation, token economy, RAG quality, evaluation, traceability, and guardrails are visible in code and docs.
- Architecture decisions, risks, and tradeoffs are documented clearly.
