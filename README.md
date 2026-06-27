# Multilingual Agentic Support Intelligence Platform

A serious AI/backend portfolio project: a multilingual AI support platform for dataset curation, RAG, LangGraph workflows, human review, evaluation, and token/cost observability.

## Problem
SaaS, gaming, entertainment, education, and other digital product teams receive support and community feedback in English, Japanese, and Chinese. They want AI support systems, but production use requires more than a chatbot: reliable retrieval, citations, permission isolation, human review, evaluation, auditability, observability, and token-cost discipline.

## Solution
This project builds a local-first internal AI platform that lets a small team import multilingual conversations, label examples, upload product knowledge, run a governed LangGraph support-agent workflow, retrieve cited evidence, generate same-language responses, route risky cases to human review, evaluate quality per language, and inspect every model call for cost, latency, cache use, and quality.

## Why Multilingual Support Matters
Japan-facing AI products often need English, Japanese, and Chinese support. The system must preserve user language, handle Japanese and Chinese without whitespace-only assumptions, and evaluate correctness, tone, safety, and language preservation separately by language.

## Why Token Economy Matters
Token cost affects product margin, latency, reliability, and adoption. This project avoids raw long-document prompts, uses retrieval and context packing, applies cheaper models to routing/classification, reserves stronger models for generation or judgment, and tracks token/cost/latency for every model call.

## Architecture Diagram
Milestone 0 documents the architecture. A visual diagram will be added during portfolio packaging.

Core pillars:
1. Multilingual Data Platform
2. Knowledge and Retrieval
3. Agent Workflow
4. Quality and Safety
5. Observability and Cost

## Demo Workflow
```text
import multilingual data
→ label examples
→ upload knowledge docs
→ run support agent
→ inspect graph trace
→ inspect token cost
→ route to human review
→ approve/edit response
→ run evaluation
→ inspect evaluation dashboard
→ serve answer through API
```

## Core Features
Phase 1 includes FastAPI, PostgreSQL + pgvector, Redis worker, Docker Compose, auth, workspace isolation, multilingual import, language detection, label editing, document ingestion, chunking, embeddings, LangGraph workflow, RAG with citations, no-source refusal, token budgets, human review, graph traces, AI run ledger, evaluation runner, cost dashboard, pytest, CI, and docs.

## LangGraph Workflow
```text
detect_language
classify_intent
retrieve_evidence
compress_context
draft_response
check_policy_and_tone
score_confidence
route_review_or_finalize
finalize_response
```

The workflow routes to human review for low confidence, missing citations, unsupported answers, unsafe output, high token cost, high safety risk, escalation need, or language-specific quality failure.

## RAG Design
RAG includes document upload, parsing, language-aware chunking, embedding generation, pgvector storage, vector search, lexical search, hybrid retrieval, metadata filtering, citation generation, retrieval trace, no-source refusal, and token-budget-aware context packing.

## Evaluation Design
Evaluation uses JSONL cases and compares direct LLM, vector-only RAG, and system v1 with hybrid RAG, compression, guardrails, and human review routing. Metrics include retrieval precision, citation accuracy, groundedness, prompt-injection blocking, permission leakage tests, language preservation, review routing accuracy, latency, prompt tokens, and estimated cost.

## Observability And Cost Tracking
The app records graph runs, graph steps, tool calls, AI runs, retrieval traces, guardrail results, audit logs, evaluation metrics, token usage, estimated cost, latency, model choice, and cache hit rate.

## Security And Workspace Isolation
Every workspace-owned entity includes `workspace_id`. Every workspace route enforces membership. Retrieval, evaluations, graph runs, cost summaries, and audit logs must not leak across workspaces.

## Tests
Automated tests must use mock LLM and embedding providers. Required coverage includes language detection, chunking, labels, prompt assembly, token budget enforcement, retrieval filtering, structured outputs, graph routing, guardrails, cost calculation, citations, auth, workspace isolation, pgvector retrieval, Redis worker, LangChain wrappers, LangGraph checkpoint/resume, evaluation runner, no-source refusal, prompt injection blocking, and long-document protection.

## How To Run Locally
Milestone 1 provides the runnable local skeleton.

Prerequisites:
- Python 3.12+
- `uv` installed in WSL and available on PATH
- WSL-native Node.js 22+ on PATH; Windows nvm/npm shims do not work reliably from WSL project paths
- Docker with Docker Compose and WSL integration enabled

Setup local dependencies with `uv` for Python and `npm` for the frontend:
```bash
make setup
```

Run database migrations after starting PostgreSQL:
```bash
make backend-migrate
```

Run checks without Docker:
```bash
make backend-test
make backend-lint
make frontend-build
make frontend-test
```

Run the full local stack:
```bash
docker compose up --build
```

Health check:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"ok","service":"api"}
```

Frontend:
```bash
http://localhost:5173
```

## Demo Data
Minimum demo data will include 30 to 60 multilingual conversation examples, 9 to 15 knowledge documents, and at least 10 evaluation cases each for English, Japanese, and Chinese. Cases must include low-risk, high-risk, no-source, prompt injection, and human-review routing scenarios.

## Tradeoffs And Limitations
V1 is local-first and intentionally avoids Kubernetes, Terraform, BigQuery, external vector databases, full enterprise SSO, fine-tuning, multimodal docs, real external integrations, multi-region scale, and complex frontend design.

## Scale Migration Path
The documented path moves from 100 local records to 1,000 with background jobs and indexes, 10,000 with batch embeddings and async evaluation, and 1M+ with split services, managed databases, object storage, analytics warehouse, dedicated vector index, horizontal workers, Cloud Run, Terraform, and monitoring. V1 documents the path but does not claim to implement it.

## Planning Documents
- `docs/README.md`: documentation map for efficient agent context loading.
- `docs/PROJECT_CONTEXT.md`: concise standing rules and non-negotiable priorities.
- `docs/architecture-tree.md`: quick architecture and tool map for orientation.
- `docs/product-spec.md`: product plan, phase scope, and portfolio story.
- `docs/milestone-plan.md`: milestone-by-milestone execution plan.
- `docs/PLANS.md`: ticket planning protocol.
- `docs/codex-workflow.md`: detailed Codex operating workflow.
- focused design docs under `docs/` for architecture, database, API, RAG, LangGraph, tools, token economy, evaluation, security, observability, scale, and tradeoffs.
