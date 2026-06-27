# Scale Path

The project starts local-first. Do not overbuild distributed infrastructure in Phase 1.

## 100 Records
- Docker Compose
- single FastAPI API
- single worker
- PostgreSQL + pgvector
- Redis

## 1,000 Records
- background ingestion jobs
- indexes
- cached retrieval
- paginated APIs

## 10,000 Records
- batch embedding jobs
- async evaluation
- worker queues
- stricter observability
- optimized retrieval

## 1 Million+ Records
Document only, not implemented in v1:
- split services
- managed PostgreSQL / Cloud SQL
- object storage
- analytics warehouse
- dedicated vector index
- horizontal workers
- Cloud Run deployment
- Terraform
- monitoring stack

## Honesty Rule
The README must clearly distinguish implemented features from future migration paths. V1 should not pretend to implement million-record infrastructure.
