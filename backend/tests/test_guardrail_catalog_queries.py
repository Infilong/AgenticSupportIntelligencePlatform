from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import event
from test_agents import create_agent, create_workspace, login, register

from app.models.agent import GraphRun
from app.models.review import GuardrailResult
from app.services.guardrail_catalog_service import GuardrailCatalogService


def test_catalog_uses_bounded_queries_and_preserves_scoped_statistics(client, db_session):
    user = register(client, "catalog-query@example.test")
    token = login(client, "catalog-query@example.test")
    workspace = create_workspace(client, token)
    foreign = create_workspace(client, token, "Foreign workspace")
    for scope in (workspace, foreign):
        agent = create_agent(client, token, scope["id"])
        run = GraphRun(workspace_id=UUID(scope["id"]), agent_config_id=UUID(agent["id"]),
                       user_id=UUID(user["id"]), input_message="Synthetic policy",
                       status="completed")
        db_session.add(run)
        db_session.flush()
        for index in range(12):
            db_session.add(GuardrailResult(
                workspace_id=run.workspace_id, graph_run_id=run.id,
                guardrail_type="custom" if scope is workspace else "foreign-only",
                passed=index >= 10, severity="medium", message=f"result {index}",
                created_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=index),
            ))
        if scope is workspace:
            for index in range(25):
                db_session.add(GuardrailResult(
                    workspace_id=run.workspace_id, graph_run_id=run.id,
                    guardrail_type=f"discovered-{index}", passed=True,
                    severity="low", message="Synthetic result",
                ))
    db_session.commit()
    statements = []

    def record(connection, cursor, statement, parameters, context, many):
        statements.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", record)
    try:
        items = GuardrailCatalogService(db_session).list_guardrails(
            workspace_id=UUID(workspace["id"]), limit=100,
        )
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert len(statements) <= 6, f"Catalog executed {len(statements)} queries"
    by_type = {item.definition.guardrail_type: item for item in items}
    assert "foreign-only" not in by_type
    custom = by_type["custom"]
    assert custom.usage.total_evaluations == 12
    assert custom.usage.failed_evaluations == 10
    assert custom.usage.pass_rate == round(2 / 12, 4)
    assert len(custom.recent_failures) == 8
    assert [row.message for row in custom.recent_failures] == [
        f"result {i}" for i in range(9, 1, -1)
    ]
