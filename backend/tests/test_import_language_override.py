import json

import pytest
from sqlalchemy import select
from test_datasets import auth_headers, create_workspace, login, register

from app.models.dataset import ConversationExample
from app.services.import_parser import ImportParseError, parse_jsonl


@pytest.mark.parametrize("source", ["jsonl", "csv"])
@pytest.mark.parametrize("language,content", [("en", "12345"), ("ja", "返金申請"), ("zh", "12345")])
def test_declared_import_language_is_preserved(client, source, language, content):
    register(client, "declared-language@example.test")
    token = login(client, "declared-language@example.test")
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}/datasets"
    messages = [{"role": "user", "content": content}]
    encoded = (json.dumps({"language": language, "messages": messages})
               if source == "jsonl" else f"role,content,language\nuser,{content},{language}\n")
    response = client.post(base + "/import", headers=auth_headers(token), json={
        "dataset_name": "Declared language", "source_type": source, "content": encoded,
    })
    assert response.status_code == 201, response.text
    dataset = response.json()["dataset"]["id"]
    result = client.get(f"{base}/{dataset}/examples", headers=auth_headers(token))
    assert result.status_code == 200
    example, = result.json()
    assert example["language"] == language
    assert example["messages"][0]["language"] == language
    assert example["messages"][0]["content"] == content


@pytest.mark.parametrize("source", ["jsonl", "csv"])
def test_invalid_declared_language_rejects_entire_batch(client, db_session, source):
    register(client, "invalid-language@example.test")
    token = login(client, "invalid-language@example.test")
    workspace = create_workspace(client, token)
    if source == "jsonl":
        content = "\n".join(json.dumps({"language": lang, "messages": [
            {"role": "user", "content": "Refund request"},
        ]}) for lang in ("en", "invalid-private-value"))
    else:
        content = ("role,content,language\nuser,Refund request,en\n"
                   "user,Refund request,invalid-private-value\n")
    response = client.post(f"/api/v1/workspaces/{workspace['id']}/datasets/import",
                           headers=auth_headers(token), json={
        "dataset_name": "Rejected", "source_type": source, "content": content,
    })
    assert response.status_code == 400
    assert "invalid-private-value" not in response.text
    assert db_session.scalar(select(ConversationExample)) is None


@pytest.mark.parametrize("value", [[], {}, 123, True])
def test_non_string_language_is_a_typed_parse_failure(value):
    with pytest.raises(ImportParseError, match="Unsupported language"):
        parse_jsonl(json.dumps({"language": value, "messages": [
            {"role": "user", "content": "Refund request"},
        ]}))
