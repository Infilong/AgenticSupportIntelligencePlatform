"""Retrieval node execution, explicit failure routing and embedding trace linkage."""

import json
import time
from uuid import UUID

from sqlalchemy import select

from app.core.language import SupportedLanguage
from app.models.agent import GraphStepStatus, ToolCall
from app.models.ai import AIRun
from app.services.embedding_attempts import EmbeddingAdmissionError
from app.services.langchain_support import chunk_payloads_to_documents, create_search_documents_tool
from app.services.retrieval_service import RetrievalError
from app.services.support_agent_state import SupportAgentState
from app.services.tool_service import ToolService


def retrieve_evidence(runner, state: SupportAgentState, *, top_k: int,
                      min_score: float) -> SupportAgentState:
    started = time.perf_counter()
    language = SupportedLanguage(state["detected_language"])
    if state.get("model_provider_failure") or state.get("model_budget_failure"):
        output: SupportAgentState = {
            "retrieved_chunks": [],
            "citations": [],
            "no_source": True,
        }
        runner._record_step("retrieve_evidence", state, output, started)
        return output
    workspace_id = UUID(state["workspace_id"])
    tool_definition = ToolService(runner.db).get_tool_definition(
        workspace_id=workspace_id, tool_name="search_documents"
    )
    tool_input = {
        "query": state["input_message"],
        "language": language.value,
        "top_k": top_k,
        "min_score": min_score,
    }
    if not tool_definition.enabled:
        output = {
            "retrieved_chunks": [],
            "citations": [],
            "no_source": True,
            "langchain_tool": "search_documents",
            "tool_disabled": "search_documents",
            "errors": [
                *state.get("errors", []),
                "search_documents disabled by workspace tool configuration",
            ],
        }
        step = runner._record_step(
            "retrieve_evidence",
            state,
            output,
            started,
            status=GraphStepStatus.failed,
            error_message="search_documents disabled by workspace tool configuration",
        )
        runner.db.add(
            ToolCall(
                workspace_id=workspace_id,
                graph_run_id=UUID(state["graph_run_id"]),
                graph_step_id=step.id,
                tool_name="search_documents",
                input_json=json.dumps(tool_input),
                output_json=json.dumps(
                    {
                        "framework": tool_definition.framework,
                        "tool_disabled": True,
                        "no_source": True,
                        "result_count": 0,
                        "timeout_ms": tool_definition.timeout_ms,
                        "max_retries": tool_definition.max_retries,
                    }
                ),
                status=GraphStepStatus.failed,
                latency_ms=max(1, int((time.perf_counter() - started) * 1000)),
            )
        )
        runner.db.commit()
        return output
    document_ids = (state.get("agent_settings") or {}).get("knowledge_document_ids")
    search_tool = create_search_documents_tool(db=runner.db, workspace_id=workspace_id,
        graph_run_id=UUID(state["graph_run_id"]), allowed_document_ids=(
            [UUID(value) for value in document_ids] if document_ids is not None else None))
    try:
        tool_output = search_tool.invoke(tool_input)
    except RetrievalError as exc:
        budget = isinstance(exc.__cause__, EmbeddingAdmissionError)
        output = {"retrieved_chunks": [], "citations": [], "no_source": True,
                  "retrieval_trace_id": str(exc.trace_id) if exc.trace_id else None,
                  "model_budget_failure" if budget else "model_provider_failure": str(exc),
                  "errors": [*state.get("errors", []), str(exc)]}
        step = runner._record_step("retrieve_evidence", state, output, started,
                                   status=GraphStepStatus.failed, error_message=str(exc))
        link_embedding_step(runner.db, step)
        runner.db.add(ToolCall(workspace_id=workspace_id, graph_run_id=step.graph_run_id,
            graph_step_id=step.id, tool_name="search_documents", input_json=json.dumps(tool_input),
            output_json=json.dumps(output), status=GraphStepStatus.failed,
            latency_ms=max(1, int((time.perf_counter() - started) * 1000))))
        runner.db.commit()
        return output
    raw_chunks = tool_output["results"]
    documents = chunk_payloads_to_documents(raw_chunks)
    chunks = []
    for chunk_payload, document in zip(raw_chunks, documents, strict=True):
        chunk = dict(chunk_payload)
        chunk["langchain_document_metadata"] = document.metadata
        chunks.append(chunk)
    output: SupportAgentState = {
        "retrieved_chunks": chunks,
        "retrieval_trace_id": tool_output["trace_id"],
        "citations": [chunk["citation"] for chunk in chunks],
        "no_source": tool_output["no_source"],
        "langchain_tool": search_tool.name,
    }
    step = runner._record_step("retrieve_evidence", state, output, started)
    link_embedding_step(runner.db, step)
    tool_started = time.perf_counter()
    runner.db.add(
        ToolCall(
            workspace_id=workspace_id,
            graph_run_id=UUID(state["graph_run_id"]),
            graph_step_id=step.id,
            tool_name="search_documents",
            input_json=json.dumps(tool_input),
            output_json=json.dumps(
                {
                    "framework": tool_output["framework"],
                    "trace_id": tool_output["trace_id"],
                    "result_count": tool_output["result_count"],
                    "langchain_document_count": len(documents),
                    "no_source": tool_output["no_source"],
                    "timeout_ms": tool_definition.timeout_ms,
                    "max_retries": tool_definition.max_retries,
                }
            ),
            status=GraphStepStatus.succeeded,
            latency_ms=max(1, int((time.perf_counter() - tool_started) * 1000)),
        )
    )
    runner.db.commit()
    return output

def link_embedding_step(db, step):
    attempts = db.scalars(select(AIRun).where(AIRun.workspace_id == step.workspace_id,
        AIRun.graph_run_id == step.graph_run_id, AIRun.purpose == "embedding_query",
        AIRun.graph_step_id.is_(None)).order_by(AIRun.created_at)).all()
    for attempt in attempts:
        attempt.graph_step_id = step.id
    if attempts:
        step.ai_run_id = attempts[0].id
