import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.conversations.schemas import Labels
from app.modules.conversations.service import parse


@pytest.mark.parametrize("label", ["ß" * 32, "İ"])
def test_normalized_label_obeys_storage_and_filter_contract(label):
    with pytest.raises(ValidationError):
        Labels(labels=[label])


def test_jsonl_preserves_unicode_separators_inside_original():
    original = "first\u2028second\u0085third"
    data = json.dumps({"original": original, "language": "en"}, ensure_ascii=False).encode()
    assert parse(data + b"\r\n")[0].original == original


def test_unpaired_surrogate_is_rejected_before_database_encoding():
    with pytest.raises(HTTPException) as error:
        parse(b'{"original":"\\ud800","language":"en"}')
    assert error.value.status_code == 422
