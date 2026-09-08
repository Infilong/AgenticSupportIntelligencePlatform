import pytest
from sqlalchemy import select
from test_datasets import auth_headers, create_workspace, login, register

from app.models.dataset import ConversationExample, ImportBatch, ImportStatus
from app.services.import_parser import parse_csv


@pytest.mark.parametrize("content", [
    "role,content\nuser,Valid refund request\nuser,Private message,unexpected field\n",
    "role,content,content\nuser,Lost private text,Retained text\n",
    'role,content\nuser,Valid refund request\nuser,"Private unterminated text\n',
    'role,content\nuser,Valid refund request\nuser,"Private quoted text"trailing\n',
])
def test_invalid_csv_shape_returns_typed_error_without_partial_rows(client, db_session, content):
    register(client, "csv-shape@example.test")
    token = login(client, "csv-shape@example.test")
    workspace = create_workspace(client, token)
    response = client.post(f"/api/v1/workspaces/{workspace['id']}/datasets/import",
                           headers=auth_headers(token), json={
        "dataset_name": "Malformed CSV", "source_type": "csv", "content": content,
    })
    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "dataset_import_failed"
    assert "private" not in response.text.lower()
    assert db_session.scalar(select(ConversationExample)) is None
    batch, = db_session.scalars(select(ImportBatch)).all()
    assert batch.status == ImportStatus.failed
    assert batch.error_message


def test_quoted_commas_and_newlines_remain_valid_csv_content():
    parsed = parse_csv('role,content\nuser,"Refund, please\nand thank you"\n')
    assert len(parsed) == 1
    assert parsed[0].messages[0].content == "Refund, please\nand thank you"


def test_escaped_quotes_remain_valid_csv_content():
    parsed = parse_csv('role,content\nuser,"Please explain ""refund pending"", thanks"\n')
    assert parsed[0].messages[0].content == 'Please explain "refund pending", thanks'
