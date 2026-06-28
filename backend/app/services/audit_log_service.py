from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import String, cast, not_, or_, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

HIGH_IMPACT_ACTION_FRAGMENTS = ("deleted", "activated", "resolved")
MEDIUM_IMPACT_ACTION_FRAGMENTS = ("reindexed", "updated", "created")


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        workspace_id: UUID,
        actor_user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_logs(
        self,
        *,
        workspace_id: UUID,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        actor: str = "all",
        impact: str = "all",
    ) -> list[AuditLog]:
        filters = [AuditLog.workspace_id == workspace_id]
        if actor == "user":
            filters.append(AuditLog.actor_user_id.is_not(None))
        elif actor == "system":
            filters.append(AuditLog.actor_user_id.is_(None))

        high_conditions = [
            AuditLog.action.ilike(f"%{fragment}%") for fragment in HIGH_IMPACT_ACTION_FRAGMENTS
        ]
        medium_conditions = [
            AuditLog.action.ilike(f"%{fragment}%") for fragment in MEDIUM_IMPACT_ACTION_FRAGMENTS
        ]
        if impact == "high":
            filters.append(or_(*high_conditions))
        elif impact == "medium":
            filters.append(or_(*medium_conditions))
        elif impact == "low":
            filters.append(not_(or_(*(high_conditions + medium_conditions))))

        normalized_search = (search or "").strip()
        if normalized_search:
            pattern = f"%{normalized_search}%"
            filters.append(
                or_(
                    AuditLog.action.ilike(pattern),
                    AuditLog.resource_type.ilike(pattern),
                    AuditLog.resource_id.ilike(pattern),
                    cast(AuditLog.actor_user_id, String).ilike(pattern),
                    AuditLog.metadata_json.ilike(pattern),
                )
            )

        statement = (
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
