from fastapi import HTTPException
from sqlalchemy import func, select

from app.modules.workspaces.models import Membership, Workspace


def membership(db, workspace_id, user_id, roles=None):
    member = db.get(Membership, (workspace_id, user_id), populate_existing=True)
    if member is None:
        raise HTTPException(404, "Workspace not found")
    if roles and member.role not in roles:
        raise HTTPException(403, "Your role does not allow this action")
    return member


def change_member(db, workspace_id, actor_id, target_id, role):
    # All membership writers serialize on the workspace, then recheck authority under the lock.
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id).with_for_update())
    if workspace is None:
        raise HTTPException(404, "Workspace not found")
    membership(db, workspace_id, actor_id, {"admin"})
    target = db.get(Membership, (workspace_id, target_id), populate_existing=True)
    if target is None:
        raise HTTPException(404, "Member not found")
    if target.role == "admin" and role != "admin":
        admins = db.scalar(
            select(func.count())
            .select_from(Membership)
            .where(Membership.workspace_id == workspace_id, Membership.role == "admin")
        )
        if admins <= 1:
            raise HTTPException(409, "Keep at least one administrator in this workspace")
    if role is None:
        db.delete(target)
    else:
        target.role = role
    db.commit()
