# Interview Explanation

## Short Pitch
I built a multilingual AI support intelligence platform for internal support teams. It imports English, Japanese, and Chinese conversations, indexes knowledge documents, runs a governed LangGraph support workflow with RAG, routes risky cases to human review, evaluates outputs by language and baseline, and tracks token cost, latency, citations, and trace data for every AI workflow.

## Why This Project Is Not A Tutorial Chatbot
- It has JWT auth and workspace isolation.
- It stores graph runs, graph steps, tool calls, retrieval traces, guardrail results, human reviews, evaluation results, and AI run ledger data.
- It compares `direct_llm`, `vector_rag`, and `system_v1` rather than relying on anecdotal demo quality.
- It treats token budget, cost, and latency as product requirements.
- It supports multilingual workflows where Japanese and Chinese cannot rely on whitespace-only assumptions.

## Architecture Story
The backend is FastAPI with SQLAlchemy, Alembic, PostgreSQL, pgvector, Redis, and Docker Compose. The frontend is a Vite/React internal operations UI. LangGraph owns the inspectable workflow. LangChain is used only where it helps with model, prompt, retriever, and tool abstractions; the application owns persistence, permissions, tracing, evaluation, and token accounting.

## Key Design Decisions
- Local-first v1 keeps the project achievable and reviewable.
- pgvector keeps relational and vector data together for the portfolio slice.
- Hybrid retrieval gives better support-policy behavior than vector-only retrieval.
- LangGraph makes each agent step inspectable and testable.
- Human review is stored as a workflow because production teams need accountability.
- Evaluation is deterministic in v1 to make CI stable; LLM-as-judge and human rubric review are future extensions.

## Questions To Be Ready For
1. How do you prevent workspace data leakage?
2. Why did you use LangGraph instead of a free-form agent?
3. How do you know RAG improved quality?
4. How do you control token cost?
5. What are the limitations of deterministic evaluation?
6. How would you scale from 1,000 to 1 million records?
7. How would you improve Japanese and Chinese retrieval in production?
8. What would you change before production deployment?

## Strong Answer Pattern
Answer with the implemented v1 first, then the future path. Example:

"In v1, every workspace-owned table has `workspace_id`, and every route uses a workspace membership dependency plus service-level workspace filters. Retrieval, evaluations, graph runs, human reviews, and costs are all scoped by workspace. At larger scale, I would add stronger audit logging, object storage, managed Cloud SQL, and automated permission regression tests in CI for every new route."
