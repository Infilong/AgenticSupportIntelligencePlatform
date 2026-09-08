"""Record observable internal tool results in the caller's action transaction."""

import json

from app.models.agent import GraphStep, ToolCall
from app.services.graph_step_ordering import persist_step


def record_action(db, proposal, latency_ms):
    step = GraphStep(workspace_id=proposal.workspace_id, graph_run_id=proposal.graph_run_id,
        step_name="apply_task_update", input_json=proposal.inputs_json,
        output_json=proposal.result_json, status="succeeded", latency_ms=latency_ms)
    persist_step(db, step, commit=False)
    db.add(ToolCall(workspace_id=proposal.workspace_id, graph_run_id=proposal.graph_run_id,
        graph_step_id=step.id, tool_name=json.loads(proposal.inputs_json)["action"],
        input_json=proposal.inputs_json, output_json=proposal.result_json,
        status="succeeded", latency_ms=latency_ms))
