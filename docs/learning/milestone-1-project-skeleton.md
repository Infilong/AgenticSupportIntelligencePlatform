# Milestone 1: Project Skeleton

## What Was Built
Milestone 1 creates the runnable foundation: FastAPI backend, TypeScript frontend shell, Docker Compose, PostgreSQL with pgvector, Redis, pytest, ruff, Makefile commands, and GitHub Actions CI.

## Why Companies Care
Production AI work still depends on reliable backend basics. A serious AI platform needs repeatable local startup, automated tests, linting, service boundaries, and CI before adding RAG, LangGraph, or model-provider logic.

## How This Project Uses It
The backend exposes only `GET /health` for now. PostgreSQL, pgvector, and Redis are available through Compose but no product schema is created yet. The frontend is a minimal shell that identifies the project without pretending product dashboards exist.

## Tradeoffs
- FastAPI gives a clear Python API foundation without adding product complexity early.
- Docker Compose is enough for the local-first v1 and avoids premature Kubernetes or cloud infrastructure.
- pgvector is introduced early so the environment supports later retrieval work, but application tables are deferred.
- The frontend stays intentionally minimal to avoid UI scope creep before backend foundations are stable.

## Failure Modes
- Adding auth, RAG, LangGraph, or AI providers during the skeleton milestone would create misleading scope.
- Docker can drift from local commands if both are not tested.
- CI can become slow or fragile if dependencies are overbuilt too early.
- A health endpoint can become too complex if it checks services before database readiness is designed.

## Project Explanation
This milestone proves I can start from a clean repository and establish a production-minded development base: API process, frontend process, database service, cache service, tests, linting, Docker, and CI. Later AI features build on this base rather than being pasted into an unreliable repo.


## Toolchain Update
Backend dependency management and test execution use `uv` so local development, CI, and Docker builds follow the same Python package workflow. WSL should use a native Linux Node.js binary on PATH rather than Windows npm shims.
