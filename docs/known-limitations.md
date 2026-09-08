# Known Limitations

## Implemented V1 Limitations
- New support tasks use the durable worker. Knowledge ingestion and some retained backend
  operations are synchronous; text/Markdown inputs are bounded.
- Embeddings default to mocks; configured OpenAI embeddings and model calls are available.
  Automated tests use synthetic providers and do not establish real semantic or answer quality.
- Evaluation uses deterministic string/citation checks, not human rubric scoring or LLM-as-judge.
- The graph checks numeric durations against cited text, but matching quantities do not prove
  factual support. Relations, negation and other claim types remain unverified; see the
  [duration contract](langgraph-workflow-design.md#numeric-duration-support).
- Demo data is representative but not yet a large realistic support corpus.
- The legacy frontend shell is removed. Current frontend modules pass the 300-line size gate;
  some backend modules retain tracked size exceptions.
- Cost values are estimates, not billing-grade accounting.

## Retrieval Limitations
- Default mock-embedding searches use lexical ranking; synthetic hash vectors do not provide
  relevance. Vector evaluation remains simulation under mocks; OpenAI mode needs a controlled
  real-provider benchmark before claiming semantic quality. Reindex after configuration changes.
- Embedding calls have monthly and graph-run admission with durable run/step ledger links.
  Owner-only uncertain-usage reconciliation is available through the API;
  owned orphaned embedding attempts can be recovered to uncertain through the owner API.
  The old Costs UI is retired. Legacy pending-call recovery, model-call ownership and external
  billing verification remain open.
- Japanese and Chinese lexical search uses simple normalization and character matching.
- No production reranker is implemented in v1.
- No dedicated external vector database is used in v1.

## Security Limitations
- V1 has JWT auth and workspace isolation, but not enterprise SSO.
- Audit logs now cover key admin and workflow actions, but they are not a full immutable event-sourcing system and do not yet cover every low-risk read operation.
- Trace responses redact selected secrets and sensitive fields; this is not universal PII detection.

## Scale Limitations
- V1 is appropriate for local small-team demos and modest datasets.
- 1M+ record scale is documented as a migration path, not implemented.
- Production deployment would need managed database, object storage, async workers, monitoring, secrets management, and infrastructure-as-code.

## Portfolio Honesty Statement
This project demonstrates production-style boundaries and workflows, but it is not claiming to be a fully deployed enterprise SaaS product. The value is in the architecture, implementation discipline, tests, traceability, evaluation, and documented scale path.
