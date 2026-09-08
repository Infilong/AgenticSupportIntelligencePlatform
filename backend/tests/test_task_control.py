from uuid import UUID

import pytest
from sqlalchemy import func, select
from test_admin_hierarchy import account
from test_task_admission import setup

from app.models.agent import Checkpoint, GraphRunStatus
from app.models.audit import AuditLog
from app.models.review import HumanReview, ReviewDecision
from app.models.task import TaskExecution
from app.models.user import User
from app.services.review_transaction import HumanReviewAlreadyResolvedError, pending_review
from app.services.task_admission import admit_task
from app.services.task_control import TaskControlError, request_stop


@pytest.mark.parametrize("status,expected", [("queued", "stopped"), ("running", "stopping"),
                                            ("needs_human_review", "stopped")])
def test_stop_transitions_are_durable_and_idempotent(client, db_session, status, expected):
    args = setup(client)
    _, run = admit_task(db_session, **args)
    run.status = status
    review = HumanReview(workspace_id=run.workspace_id, graph_run_id=run.id,
                         reason="QA", reviewer_decision=ReviewDecision.pending)
    if status == "needs_human_review":
        db_session.add(review)
    db_session.commit()
    kwargs = dict(workspace_id=run.workspace_id, run_id=run.id, user_id=args["user_id"])
    stopped = request_stop(db_session, **kwargs)
    assert stopped.status == expected
    assert (stopped.completed_at is None) is (status == "running")
    execution = db_session.get(TaskExecution, run.id)
    assert execution.stop_requested_at is not None
    assert execution.stopped_by_user_id == args["user_id"]
    assert request_stop(db_session, **kwargs).status == expected
    assert db_session.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.action == "task_run.stop_requested")) == 1
    assert db_session.scalar(select(func.count()).select_from(Checkpoint).where(
        Checkpoint.checkpoint_key == "stop_requested")) == 1
    if status == "needs_human_review":
        with pytest.raises(HumanReviewAlreadyResolvedError):
            pending_review(db_session, workspace_id=run.workspace_id, review_id=review.id,
                           reviewer=db_session.get(User, args["user_id"]))


def test_stop_denies_outsiders_and_does_not_rewrite_completed_output(client, db_session):
    args = setup(client)
    _, run = admit_task(db_session, **args)
    outsider, _, _ = account(client, "stop-outsider")
    with pytest.raises(TaskControlError, match="permission"):
        request_stop(db_session, workspace_id=run.workspace_id, run_id=run.id,
                     user_id=UUID(outsider))
    db_session.rollback()
    run.status = GraphRunStatus.completed
    run.final_answer = "Already published"
    db_session.commit()
    with pytest.raises(TaskControlError, match="Finished work"):
        request_stop(db_session, workspace_id=run.workspace_id, run_id=run.id,
                     user_id=args["user_id"])
    db_session.rollback()
    assert run.final_answer == "Already published"
    assert db_session.get(TaskExecution, run.id).stop_requested_at is None
