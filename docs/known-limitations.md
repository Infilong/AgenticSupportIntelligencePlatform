# Known Limitations

## Implemented V1 Limitations
- The system is local-first and synchronous in several places where production should use background queues.
- Embeddings and model providers are deterministic mocks for tests and local portfolio safety.
- Evaluation uses deterministic string/citation checks, not human rubric scoring or LLM-as-judge.
- Demo data is representative but not yet a large realistic support corpus.
- The frontend is intentionally compact and can be decomposed into components after demo review.
- Cost values are estimates, not billing-grade accounting.

## Retrieval Limitations
- Japanese and Chinese lexical search uses simple normalization and character matching.
- No production reranker is implemented in v1.
- No dedicated external vector database is used in v1.

## Security Limitations
- V1 has JWT auth and workspace isolation, but not enterprise SSO.
- Audit logs now cover key admin and workflow actions, but they are not a full immutable event-sourcing system and do not yet cover every low-risk read operation.
- PII detection/redaction is postponed to Phase 2.

## Scale Limitations
- V1 is appropriate for local small-team demos and modest datasets.
- 1M+ record scale is documented as a migration path, not implemented.
- Production deployment would need managed database, object storage, async workers, monitoring, secrets management, and infrastructure-as-code.

## Portfolio Honesty Statement
This project demonstrates production-style boundaries and workflows, but it is not claiming to be a fully deployed enterprise SaaS product. The value is in the architecture, implementation discipline, tests, traceability, evaluation, and documented scale path.
