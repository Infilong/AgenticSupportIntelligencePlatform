from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    actor_user_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    metadata_json: str
    created_at: datetime
