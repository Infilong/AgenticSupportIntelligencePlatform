# Architecture Tree

Use this file for quick orientation. It summarizes the architecture, tools, current implementation state, and future milestones. Detailed decisions remain in the focused design docs.

## System Tree

```text
Multilingual Agentic Support Intelligence Platform
|-- Product Goal
|   |-- Internal AI support intelligence platform
|   |-- Supports English, Japanese, and Chinese in v1
|   |-- Local-first for a small team
|   `-- Designed for future scale without overbuilding v1
|
|-- Runtime Architecture
|   |-- Frontend
|   |   |-- React
|   |   |-- TypeScript
|   |   |-- Vite
|   |   `-- Future UI pages
|   |       |-- login
|   |       |-- workspaces
|   |       |-- datasets
|   |       |-- documents
|   |       |-- agent run
|   |       |-- graph trace viewer
|   |       |-- evaluations
|   |       `-- cost dashboard
|   |
|   |-- Backend API
|   |   |-- Python
|   |   |-- FastAPI
|   |   |-- Pydantic and pydantic-settings
|   |   |-- SQLAlchemy
|   |   |-- Alembic
|   |   |-- JWT auth
|   |   |-- Workspace permission dependencies
|   |   |-- pytest
|   |   `-- ruff
|   |
|   |-- Database
|   |   |-- PostgreSQL
|   |   |-- pgvector
|   |   |-- Alembic migrations
|   |   `-- Workspace-scoped data model
|   |
|   |-- Async And Background Processing
|   |   |-- Redis
|   |   `-- Future worker: Celery, RQ, or Arq
|   |
|   |-- AI Layer
|   |   |-- LangChain
|   |   |   |-- model abstraction
|   |   |   |-- prompt templates
|   |   |   |-- structured outputs
|   |   |   |-- retrievers
|   |   |   `-- tools
|   |   |-- LangGraph
|   |   |   |-- support-agent workflow
|   |   |   |-- graph state
|   |   |   |-- conditional routing
|   |   |   |-- checkpoints
|   |   |   `-- human review routing
|   |   |-- OpenAI-compatible provider abstraction
|   |   |-- Optional Gemini provider later
|   |   |-- Mock LLM provider for tests
|   |   `-- Mock embedding provider for tests
|   |
|   `-- DevOps And Local Runtime
|       |-- Docker Compose
|       |-- Dockerfiles
|       |-- uv for Python dependency management
|       |-- npm for frontend dependency management
|       |-- Makefile
|       |-- GitHub Actions CI
|       `-- .env.example
|
|-- Five Architecture Pillars
|   |-- 1. Multilingual Data Platform
|   |   |-- datasets
|   |   |-- imports
|   |   |-- examples
|   |   |-- messages
|   |   |-- language detection
|   |   `-- labels
|   |
|   |-- 2. Knowledge And Retrieval
|   |   |-- documents
|   |   |-- document versions
|   |   |-- chunks
|   |   |-- embeddings
|   |   |-- pgvector search
|   |   |-- lexical search
|   |   |-- hybrid retrieval
|   |   |-- context packing
|   |   `-- citations
|   |
|   |-- 3. Agent Workflow
|   |   |-- LangGraph runtime
|   |   |-- graph runs
|   |   |-- graph steps
|   |   |-- tools
|   |   |-- human review
|   |   `-- checkpoints
|   |
|   |-- 4. Quality And Safety
|   |   |-- guardrails
|   |   |-- no-source refusal
|   |   |-- prompt injection checks
|   |   |-- citation validation
|   |   |-- language preservation
|   |   |-- confidence scoring
|   |   `-- evaluation
|   |
|   `-- 5. Observability And Cost
|       |-- AI run ledger
|       |-- token accounting
|       |-- cost estimation
|       |-- latency tracking
|       |-- model choice tracking
|       |-- cache hit tracking
|       |-- retrieval traces
|       |-- graph traces
|       `-- audit logs
|
|-- Main LangGraph Workflow
|   |-- detect_language
|   |-- classify_intent
|   |-- retrieve_evidence
|   |-- compress_context
|   |-- draft_response
|   |-- check_policy_and_tone
|   |-- score_confidence
|   |-- route_review_or_finalize
|   `-- finalize_response
|
|-- Current Implemented Milestones
|   |-- Milestone 0: governance, architecture, and planning docs
|   |-- Milestone 1: runnable FastAPI, React/Vite, Docker, PostgreSQL, pgvector, Redis, CI
|   |-- Milestone 2: users, JWT auth, workspaces, membership checks, permission tests
|   `-- Milestone 3: dataset import, multilingual examples, language detection, labels
|
`-- Future Milestones
    |-- Milestone 4: knowledge document ingestion
    |-- Milestone 5: retrieval and citations
    |-- Milestone 6: AI run ledger and token budget planner
    |-- Milestone 7: LangGraph support-agent workflow
    |-- Milestone 8: guardrails and human review
    |-- Milestone 9: evaluation runner
    |-- Milestone 10: frontend trace and evaluation UI
    `-- Milestone 11: portfolio packaging
```

## Quick Tool List

```text
Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PyJWT, pytest, ruff
Frontend: React, TypeScript, Vite, npm
Database: PostgreSQL, pgvector
Queue/cache: Redis, future Celery/RQ/Arq worker
AI: LangChain, LangGraph, OpenAI-compatible provider abstraction, mock LLM/embedding providers
DevOps: Docker Compose, Dockerfiles, uv, Makefile, GitHub Actions CI
Docs/process: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/PLANS.md, docs/tickets/*, docs/learning/*
```

## Boundary Summary

```text
FastAPI owns auth, workspace isolation, API boundaries, persistence, evaluation, traces, and token/cost accounting.
LangChain is used only where it adds value for model, prompt, retriever, structured-output, and tool abstractions.
LangGraph owns inspectable workflow orchestration, not uncontrolled autonomous behavior.
PostgreSQL/pgvector stores relational and vector data under workspace boundaries.
Redis supports background jobs and future async processing.
Every future AI call must be traceable, evaluable, and token-cost controlled.
```

## When To Read This File

Read this file when you need quick orientation, milestone context, tool overview, or an interview-level architecture summary. For implementation details, read the focused subsystem docs listed in `docs/README.md`.
