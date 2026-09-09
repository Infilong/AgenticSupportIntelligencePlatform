"""Admission of a new linked attempt; no prior approval or provider context is reused."""

import uuid
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select

from app.jobs.models import Job
from app.jobs.queue import authorize, enqueue
from app.modules.support.context import digest
from app.modules.support.models import Message, SupportRun
from app.modules.support.reading import visible_state
from app.modules.support.service import cancel_run, get_run
from app.modules.workspaces.service import membership

MAX_ATTEMPTS = 10
INPUT_LIMIT = 1000
SEPARATOR = "\n\nCustomer clarification:\n"


class AttemptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["retry", "clarify"]
    clarification: str | None = Field(None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def valid_details(self):
        if self.action == "retry" and self.clarification is not None:
            raise ValueError("Retry cannot change the processing input")
        if self.action == "clarify" and (
            self.clarification is None or not self.clarification.strip() or "\x00" in self.clarification
        ):
            raise ValueError("Enter additional customer details without NUL characters")
        return self


def create(db, workspace_id, actor_id, parent_id, key, data):
    authorize(db, workspace_id, actor_id)
    parent = get_run(db, workspace_id, parent_id)
    message = db.scalar(
        select(Message)
        .where(Message.id == parent.message_id, Message.workspace_id == workspace_id)
        .with_for_update()
    )
    membership(db, workspace_id, message.actor_id, {"operator", "admin"})
    identity = digest({"actor": str(actor_id), "parent": str(parent_id), **data.model_dump()})
    previous = db.scalar(
        select(SupportRun).where(SupportRun.workspace_id == workspace_id, SupportRun.submission_key == key)
    )
    if previous is not None:
        if previous.submission_hash != identity:
            raise HTTPException(409, "Submission key already belongs to another attempt")
        return {"message_id": message.id, "run_id": previous.id, "job_id": previous.job_id}
    latest = db.scalar(
        select(SupportRun)
        .where(SupportRun.workspace_id == workspace_id, SupportRun.message_id == message.id)
        .order_by(SupportRun.attempt_number.desc())
        .limit(1)
    )
    if latest.id != parent.id:
        raise HTTPException(409, "A newer attempt exists; open it before continuing")
    job = db.get(Job, parent.job_id)
    state = visible_state(parent, job)
    if state in {"queued", "running"}:
        raise HTTPException(409, "Cancel active processing before creating another attempt")
    if data.action == "retry" and not (
        state in {"failed", "cancelled", "rejected"} or parent.outcome == "insufficient_evidence"
    ):
        raise HTTPException(
            409, "Retry is available for unsuccessful attempts; add details to clarify instead"
        )
    if parent.attempt_number >= MAX_ATTEMPTS:
        raise HTTPException(409, "This message has reached its ten-attempt limit")
    processing_input = parent.input_text
    if data.action == "clarify":
        processing_input += SEPARATOR + data.clarification
    if len(processing_input) > INPUT_LIMIT:
        raise HTTPException(
            422, "Original input and added details must fit the 1,000-character processing limit"
        )
    if state in {"waiting_for_input", "awaiting_review"}:
        cancel_run(db, workspace_id, actor_id, parent.id)
    run_id = uuid.uuid4()
    child_job = enqueue(
        db, workspace_id, actor_id, "support_run", f"support:{run_id}", {"run_id": str(run_id)}, priority=0
    )
    child = SupportRun(
        id=run_id,
        workspace_id=workspace_id,
        message_id=message.id,
        job_id=child_job.id,
        creator_id=actor_id,
        parent_run_id=parent.id,
        attempt_number=parent.attempt_number + 1,
        attempt_kind=data.action,
        input_text=processing_input,
        clarification=data.clarification,
        submission_key=key,
        submission_hash=identity,
    )
    db.add(child)
    db.flush()
    return {"message_id": message.id, "run_id": child.id, "job_id": child.job_id}
