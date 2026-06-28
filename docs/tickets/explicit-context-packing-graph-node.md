# Explicit Context Packing Graph Node

## Goal
Make token-aware context packing visible as a first-class LangGraph workflow step instead of hiding retrieved-context trimming inside `draft_response`.

## Context
The active product goal requires agents, graph state, checkpoints, token economy, traceability, and debugging surfaces to be first-class. Before this ticket, the runtime retrieved evidence and then drafted directly. If context exceeded the draft model budget, trimming happened inside the draft node. That made the graph less honest: token economy was real, but not easy to inspect as its own state transition.

## Change Made
Added a deterministic `compress_context` LangGraph node between `retrieve_evidence` and `draft_response`.

The node now records:

- selected packed chunks;
- packed citations;
- token budget action;
- trimmed context count;
- planned prompt, completion, and total tokens;
- model and context-window limit used for planning;
- checkpoint data including packed-context count.

`draft_response` now consumes `packed_context_chunks` instead of trimming retrieved chunks itself. It still performs a defensive budget check before the model call, but the normal context-packing decision is inspectable in the trace before drafting.

## Files Changed
- `backend/app/services/support_agent_graph.py`
- `backend/app/services/support_agent_state.py`
- `backend/app/services/agent_service.py`
- `backend/app/api/v1/agents.py`
- `backend/tests/test_agents.py`
- `frontend/src/App.tsx`

## Backend/API Impact
- Runtime graph expanded from 7 to 8 nodes.
- Workflow metadata now reports `compress_context` and 10 graph edges.
- Trace checkpoints now include `packed_context_count`.
- Trace signal rendering now recognizes context token totals and packed-context chunks.

## Design Reasoning
This is intentionally deterministic, not an LLM summarization step. The v1 product should prove token economy without adding another model call or fake compression. Later work can replace deterministic packing with cached compression/reranking, but the interface and graph step are now already in the right place.

## Validation
Validated in this ticket:

- `cd backend && uv run pytest -s -q tests/test_agents.py tests/test_langchain_support.py` -> 30 passed, 1 warning.
- `cd backend && uv run ruff check app/services/support_agent_graph.py app/services/support_agent_state.py app/services/agent_service.py app/api/v1/agents.py tests/test_agents.py` -> passed.
- `cd frontend && npm run build` -> passed.

## Human Review Checklist
- Run an agent and open Trace.
- Confirm `compress_context` appears between retrieval and drafting.
- Confirm packed-context token fields are visible in the selected node output signals/raw output.
- Confirm draft model calls still record AI run tokens/cost and use the packed evidence.
- Confirm no raw long document is sent directly to the model.

## Interview Notes
This ticket is a strong example of production AI-platform thinking: token economy should not be a hidden helper function. It should be represented in the workflow, persisted as a graph step, inspectable in trace, and testable without real model calls.
