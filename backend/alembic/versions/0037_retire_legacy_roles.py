"""Move existing memberships to the four-role product contract, retaining audit history."""

from alembic import op

revision = "0037_retire_legacy_roles"
down_revision = "0036_task_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE workspace_members IN SHARE ROW EXCLUSIVE MODE")
    op.execute("""
        INSERT INTO audit_logs
            (id, workspace_id, actor_user_id, action, resource_type,
             resource_id, metadata_json, created_at)
        SELECT gen_random_uuid(), workspace_id, NULL, 'workspace.role_migrated',
               'workspace_member', id::text,
               json_build_object('migration', '0037_retire_legacy_roles',
                   'user_id', user_id, 'previous_role', role::text,
                   'new_role', CASE WHEN role::text = 'reviewer'
                                    THEN 'operator' ELSE 'admin' END)::text,
               CURRENT_TIMESTAMP
        FROM workspace_members WHERE role::text IN ('reviewer', 'member', 'developer')
    """)
    op.execute("""
        UPDATE workspace_members
        SET role = (CASE WHEN role::text = 'reviewer'
                        THEN 'operator' ELSE 'admin' END)::workspacerole
        WHERE role::text IN ('reviewer', 'member', 'developer')
    """)
    op.create_check_constraint(
        "ck_workspace_member_supported_role",
        "workspace_members",
        "role::text IN ('viewer', 'operator', 'admin', 'owner')",
    )


def downgrade() -> None:
    raise RuntimeError(
        "Role retirement changes authority; use forward repair or verified backup restore"
    )
