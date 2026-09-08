"""Opposing folder moves must remain acyclic with concurrent stale ORM sessions."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.models.folder import ResourceFolder
from app.services.folder_service import ResourceFolderInvalidTypeError, ResourceFolderService

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def test_opposing_parent_moves_admit_only_one(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        folders = [ResourceFolder(workspace_id=ids[0], created_by_user_id=ids[2][0],
                                  resource_type="knowledge_document", name=name)
                   for name in ("A", "B")]
        db.add_all(folders)
        db.commit()
        folder_ids = [folder.id for folder in folders]
    ready = Barrier(2)

    def move(index):
        with Session(engine) as db:
            # Retain both instances so validation cannot accidentally rely on refreshed cache.
            cached = list(db.scalars(select(ResourceFolder)).all())
            assert all(folder.parent_folder_id is None for folder in cached)
            ready.wait(timeout=10)
            try:
                ResourceFolderService(db).update_folder(
                    workspace_id=ids[0], folder_id=folder_ids[index], name=None,
                    actor_user_id=ids[2][0],
                    parent_folder_id=folder_ids[1 - index],
                )
                return "accepted"
            except ResourceFolderInvalidTypeError:
                db.rollback()
                return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(move, index) for index in range(2)]
        outcomes = [future.result(timeout=15) for future in futures]
    assert sorted(outcomes) == ["accepted", "rejected"]
    with Session(engine) as db:
        parents = dict(db.execute(select(ResourceFolder.id, ResourceFolder.parent_folder_id)).all())
        assert sum(parent is None for parent in parents.values()) == 1
        for folder_id, parent_id in parents.items():
            if parent_id is not None:
                assert parent_id != folder_id
                assert parents[parent_id] is None


def test_stale_session_can_restore_parent_after_competing_move(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        folders = [ResourceFolder(workspace_id=ids[0], created_by_user_id=ids[2][0],
                                  resource_type="knowledge_document", name=name)
                   for name in ("Child", "Original", "Other")]
        db.add_all(folders)
        db.flush()
        folders[0].parent_folder_id = folders[1].id
        db.commit()
        child, original, other = [folder.id for folder in folders]
    with Session(engine) as stale:
        cached = stale.get(ResourceFolder, child)
        assert cached.parent_folder_id == original
        with Session(engine) as competing:
            ResourceFolderService(competing).update_folder(
                workspace_id=ids[0], folder_id=child, name=None, parent_folder_id=other,
                actor_user_id=ids[2][0],
            )
        ResourceFolderService(stale).update_folder(
            workspace_id=ids[0], folder_id=child, name=None, parent_folder_id=original,
            actor_user_id=ids[2][0],
        )
    with Session(engine) as db:
        assert db.get(ResourceFolder, child).parent_folder_id == original
