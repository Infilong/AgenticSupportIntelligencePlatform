from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.identity.models import User
from app.modules.workspaces.models import Membership, Workspace
from app.modules.workspaces.service import change_member, membership

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


class RoleChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["viewer", "operator", "admin"]


@router.get("")
def list_workspaces(user: CurrentUser, db: Database):
    rows = db.execute(
        select(Workspace, Membership.role)
        .join(Membership)
        .where(Membership.user_id == user.id)
        .order_by(Workspace.name)
        .limit(100)
    )
    return [{"id": str(workspace.id), "name": workspace.name, "role": role} for workspace, role in rows]


@router.get("/{workspace_id}")
def get_workspace(workspace_id: UUID, user: CurrentUser, db: Database):
    member = membership(db, workspace_id, user.id)
    workspace = db.get(Workspace, workspace_id)
    return {"id": str(workspace.id), "name": workspace.name, "role": member.role}


@router.get("/{workspace_id}/members")
def list_members(workspace_id: UUID, user: CurrentUser, db: Database, offset: int = 0):
    membership(db, workspace_id, user.id, {"admin"})
    rows = db.execute(
        select(User, Membership.role)
        .join(Membership)
        .where(Membership.workspace_id == workspace_id)
        .order_by(User.email)
        .offset(max(0, offset))
        .limit(100)
    )
    return [
        {"id": str(member.id), "email": member.email, "display_name": member.display_name, "role": role}
        for member, role in rows
    ]


@router.patch("/{workspace_id}/members/{user_id}", status_code=204)
def update_member(workspace_id: UUID, user_id: UUID, body: RoleChange, user: CurrentUser, db: Database):
    change_member(db, workspace_id, user.id, user_id, body.role)


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
def remove_member(workspace_id: UUID, user_id: UUID, user: CurrentUser, db: Database):
    change_member(db, workspace_id, user.id, user_id, None)
