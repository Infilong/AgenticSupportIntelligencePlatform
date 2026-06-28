from datetime import datetime

from pydantic import BaseModel


class AttentionItemResponse(BaseModel):
    id: str
    category: str
    severity: str
    title: str
    detail: str
    count: int
    action_label: str
    target_tab: str
    target_id: str | None = None
    created_at: datetime | None = None


class AttentionSummaryResponse(BaseModel):
    workspace_id: str
    total_items: int
    critical_count: int
    warning_count: int
    info_count: int
    pending_reviews: int
    assigned_to_me_reviews: int
    items: list[AttentionItemResponse]
