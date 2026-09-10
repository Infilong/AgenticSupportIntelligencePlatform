"""Workspace defaults and explicit development provider configuration, never credentials."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.core.settings import GenerationSettings
from app.jobs.queue import authorize
from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.knowledge.selection import DEFAULT_STRATEGY
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.service import membership
from app.providers.local_embeddings import MODEL as EMBEDDING_MODEL
from app.providers.local_embeddings import REVISION as EMBEDDING_REVISION
from app.providers.local_reranker import MODEL as RERANKER_MODEL
from app.providers.local_reranker import REVISION as RERANKER_REVISION

router = APIRouter(prefix="/api/workspaces/{workspace_id}/settings", tags=["workspaces"])


class ProcessingDefaults(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_language: Literal["en", "ja", "zh"]


class WorkspaceSettings(ProcessingDefaults):
    generation_mode: str
    automatic_generation_available: bool
    embedding_model: str
    embedding_revision: str
    reranker_model: str
    reranker_revision: str
    retrieval_strategy: str


def projection(workspace):
    configuration = GenerationSettings()
    automatic = configuration.generation_mode == "local_ollama"
    return {
        "default_language": workspace.default_language,
        "generation_mode": "local_ollama" if automatic else "codex_assisted_development",
        "automatic_generation_available": automatic,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_revision": EMBEDDING_REVISION,
        "reranker_model": RERANKER_MODEL,
        "reranker_revision": RERANKER_REVISION,
        "retrieval_strategy": DEFAULT_STRATEGY,
    }


@router.get("", response_model=WorkspaceSettings)
def settings(workspace_id: UUID, user: CurrentUser, db: Database):
    membership(db, workspace_id, user.id, {"admin"})
    return projection(db.get(Workspace, workspace_id))


@router.put("", response_model=WorkspaceSettings)
def change_defaults(workspace_id: UUID, data: ProcessingDefaults, user: CurrentUser, db: Database):
    authorize(db, workspace_id, user.id)
    membership(db, workspace_id, user.id, {"admin"})
    workspace = db.get(Workspace, workspace_id)
    workspace.default_language = data.default_language
    result = projection(workspace)
    db.commit()
    return result
