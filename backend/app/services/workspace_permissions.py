"""Workspace permissions; legacy roles retain their original authority."""

from app.models.workspace import WorkspaceRole

BASE_PERMISSIONS = [
    "workspace:read",
    "tasks:read",
    "settings:read",
]

VIEWER_PERMISSIONS = [
    *BASE_PERMISSIONS,
    "data:read",
    "knowledge:read",
    "agents:read",
    "traces:read",
    "reviews:read",
    "evaluations:read",
    "costs:read",
]

REVIEWER_PERMISSIONS = [
    *BASE_PERMISSIONS,
    "knowledge:read",
    "agents:read",
    "traces:read",
    "reviews:read",
    "costs:read",
    "reviews:resolve",
]

DEVELOPER_PERMISSIONS = [
    *VIEWER_PERMISSIONS,
    "tools:read",
    "guardrails:read",
    "prompts:read",
    "models:read",
    "system:read",
    "data:write",
    "knowledge:write",
    "agents:run",
    "agents:configure",
    "tools:configure",
    "evaluations:run",
    "prompts:write",
    "resource_folders:manage",
]

MEMBER_PERMISSIONS = [
    *VIEWER_PERMISSIONS,
    "tools:read",
    "guardrails:read",
    "system:read",
    "data:write",
    "knowledge:write",
    "agents:run",
    "agents:configure",
    "reviews:resolve",
    "evaluations:run",
]

OWNER_PERMISSIONS = [
    *DEVELOPER_PERMISSIONS,
    "reviews:resolve",
    "members:read",
    "audit:read",
    "budget_policy:read",
    "workspace:manage",
    "resources:delete",
    "agents:delete",
    "models:write",
    "guardrails:configure",
    "budget_policy:manage",
]

ROLE_PERMISSIONS = {
    WorkspaceRole.owner: OWNER_PERMISSIONS,
    WorkspaceRole.developer: DEVELOPER_PERMISSIONS,
    WorkspaceRole.member: MEMBER_PERMISSIONS,
    WorkspaceRole.reviewer: REVIEWER_PERMISSIONS,
    WorkspaceRole.viewer: VIEWER_PERMISSIONS,
}

OPERATOR_PERMISSIONS = [*VIEWER_PERMISSIONS, "agents:run", "reviews:resolve"]
ADMIN_PERMISSIONS = [
    *OPERATOR_PERMISSIONS, "knowledge:write", "agents:configure", "agents:delete",
    "resources:delete", "resource_folders:manage", "models:read", "members:read",
    "members:manage",
]
ROLE_PERMISSIONS[WorkspaceRole.operator] = OPERATOR_PERMISSIONS
ROLE_PERMISSIONS[WorkspaceRole.admin] = ADMIN_PERMISSIONS
OWNER_PERMISSIONS.append("members:manage")

ARCHIVED_WORKSPACE_ALLOWED_PERMISSIONS = [
    "workspace:read",
    "workspace:manage",
    "settings:read",
    "tasks:read",
    "members:read",
    "audit:read",
    "data:read",
    "knowledge:read",
    "agents:read",
    "traces:read",
    "reviews:read",
    "evaluations:read",
    "costs:read",
    "budget_policy:read",
    "tools:read",
    "guardrails:read",
    "prompts:read",
    "models:read",
    "system:read",
]


