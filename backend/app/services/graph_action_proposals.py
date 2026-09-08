"""Propose bounded internal updates from already-accounted agent outputs."""

from app.models.task import TaskExecution
from app.schemas.task_action import TaskActionInput
from app.services.task_actions import TaskActionError, stage_proposal


def propose_task_updates(db, run, state) -> bool:
    if db.get(TaskExecution, run.id) is None:
        return False
    allowed = (state.get("agent_settings") or {}).get("allowed_actions", [])
    proposals = []
    if "set_category" in allowed and state.get("intent"):
        proposals.append(TaskActionInput(action="set_category", value=state["intent"]))
    if "add_note" in allowed and state.get("draft_answer"):
        # Never silently truncate an approved payload or drop its citation.
        if len(state["draft_answer"]) > 2000:
            raise TaskActionError("Proposed internal note exceeds the 2000-character limit.")
        proposals.append(TaskActionInput(action="add_note", value=state["draft_answer"]))
    for inputs in proposals:
        stage_proposal(db, run=run, inputs=inputs)
    return bool(proposals)
