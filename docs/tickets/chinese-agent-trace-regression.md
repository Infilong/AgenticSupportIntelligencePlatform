# Chinese Agent Trace Regression

## Goal
Prove the Chinese knowledge path works end to end: upload Chinese policy text, run a Chinese support query, retrieve Chinese evidence, finalize in Chinese, and expose the evidence in the graph trace.

## Context
After improving CJK chunking and adding multilingual demo templates, the remaining risk was that the app looked multilingual in isolated pieces but did not prove a Chinese query could pass through the agent workflow with traceable RAG evidence.

## Bug Found
The new regression exposed a deterministic mock-answer bug: Chinese refund queries could return the privacy-escalation answer when the retrieved policy also contained privacy terms. The answer generator was letting incidental terms in evidence override the classified user intent.

## Implementation
- Added `test_support_agent_uses_chinese_knowledge_in_trace`.
- The test uploads Chinese refund/security/privacy policy text, runs a Chinese refund question, asserts finalization in Chinese, and inspects the trace retrieval step.
- The trace assertions prove retrieved chunks are Chinese, contain refund evidence, include the Chinese document citation, and were produced through the LangChain `StructuredTool` path.
- Updated deterministic mock answer priority so explicit classified intent wins before fallback keyword matching.
- Kept privacy and Japanese security regressions passing.

## Validation
- `cd backend && uv run ruff check app/services/support_agent_graph.py tests/test_agents.py`
- `cd backend && uv run pytest -s -q tests/test_agents.py::test_support_agent_uses_chinese_knowledge_in_trace tests/test_agents.py::test_support_agent_routes_privacy_complaint_to_human_review tests/test_agents.py::test_support_agent_answers_security_policy_in_japanese`
- `cd backend && uv run pytest -s -q tests/test_agents.py tests/test_retrieval.py tests/test_knowledge_documents.py`
- `cd frontend && npm run build`

## Results
- Ruff passed.
- Targeted multilingual agent tests passed: 3 passed, 1 existing Starlette/httpx warning.
- Broader backend agent/retrieval/knowledge subset passed: 42 passed, 1 existing Starlette/httpx warning.
- Frontend build passed.

## Design Reasoning
For a professional AI platform, same-language RAG cannot be a UI-only claim. The trace must prove which evidence was retrieved, which language was used, and whether the workflow finalized or routed to review. Intent should control deterministic fallback behavior; retrieved evidence can enrich the answer, but unrelated terms in a multi-topic policy should not override the classified task.

## Human Review Checklist
- Run the Chinese refund scenario from the browser after uploading/indexing the Chinese template.
- Open Runs / Traces and confirm the retrieval step shows Chinese chunks and citations.
- Confirm the final answer is Chinese and about refunds, not privacy escalation.
