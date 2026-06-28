from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

HealthStatus = Literal["ok", "warning", "critical", "not_configured"]


class SystemHealthCheck(BaseModel):
    id: str
    label: str
    status: HealthStatus
    message: str


class SystemHealthMetric(BaseModel):
    label: str
    value: str | int | float
    status: HealthStatus = "ok"
    detail: str | None = None


class SystemHealthSection(BaseModel):
    id: str
    title: str
    status: HealthStatus
    summary: str
    metrics: list[SystemHealthMetric]


class SystemHealthResponse(BaseModel):
    workspace_id: UUID
    generated_at: datetime
    overall_status: HealthStatus
    checks: list[SystemHealthCheck]
    sections: list[SystemHealthSection]
