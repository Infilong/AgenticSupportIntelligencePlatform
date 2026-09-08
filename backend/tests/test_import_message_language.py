import json

import pytest
from test_datasets import auth_headers, create_workspace, login, register


@pytest.mark.parametrize("language,anchor", [
    ("en", "Please send your order number."),
    ("ja", "注文番号を教えてください。"),
    ("zh", "请提供您的订单编号。"),
])
def test_neutral_replies_inherit_only_their_conversation_language(client, language, anchor):
    register(client, "neutral-message@example.test")
    token = login(client, "neutral-message@example.test")
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}/datasets"
    messages = [{"role": "user", "content": "12345"},
                {"role": "assistant", "content": anchor},
                {"role": "user", "content": "👍"}]
    response = client.post(base + "/import", headers=auth_headers(token), json={
        "dataset_name": "Order conversation", "source_type": "jsonl",
        "content": json.dumps({"messages": messages}, ensure_ascii=False),
    })
    assert response.status_code == 201, response.text
    dataset_id = response.json()["dataset"]["id"]
    listed = client.get(f"{base}/{dataset_id}/examples", headers=auth_headers(token))
    assert listed.status_code == 200
    example, = listed.json()
    assert example["language"] == language
    assert {row["content"] for row in example["messages"]} == {row["content"] for row in messages}
    assert all(row["language"] == language for row in example["messages"])
