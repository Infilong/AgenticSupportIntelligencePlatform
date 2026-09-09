"""Admission remains serialized at the supported 50,000-message workspace boundary."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.support.models import Message, SupportRun
from app.modules.support.schemas import MessageInput
from app.modules.support.service import create_message
from tests.integration.capacity_data import seed_capacity


def test_concurrent_admission_stops_at_50000_and_replays_without_another_job(system):
    workspace, actor = system["workspace"], system["users"]["operator"].id
    seed_capacity(system["engine"], workspace, actor, 49999)
    barrier = Barrier(2)
    data = MessageInput(original="Capacity boundary request", language="en")

    def submit(index):
        barrier.wait(timeout=10)
        try:
            with Session(system["engine"]) as db, db.begin():
                created = create_message(db, workspace, actor, data, f"boundary-{index}")
            return 202, index, created
        except HTTPException as error:
            return error.status_code, index, None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert sorted(item[0] for item in results) == [202, 409]
    _, index, created = next(item for item in results if item[0] == 202)
    with Session(system["engine"]) as db, db.begin():
        before = [db.scalar(select(func.count()).select_from(model)) for model in (Message, SupportRun, Job)]
        assert before[0] == 50000
        assert create_message(db, workspace, actor, data, f"boundary-{index}") == created
        after = [db.scalar(select(func.count()).select_from(model)) for model in (Message, SupportRun, Job)]
        assert after == before
