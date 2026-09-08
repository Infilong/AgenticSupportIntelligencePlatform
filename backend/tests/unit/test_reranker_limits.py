from unittest.mock import Mock

import pytest

from app.providers.local_reranker import LocalReranker


@pytest.mark.parametrize(
    "query,passages",
    [("", ["text"]), ("x", []), ("x", ["text"] * 21), ("x" * 1001, ["text"]), ("x", ["y" * 8001])],
)
def test_reranking_bounds_reject_before_loading(query, passages):
    provider = LocalReranker()
    provider.load = Mock(side_effect=AssertionError("must not dispatch"))
    with pytest.raises(ValueError):
        provider.score(query, passages)
    provider.load.assert_not_called()
