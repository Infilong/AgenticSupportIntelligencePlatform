from unittest.mock import Mock

import pytest

from app.providers.local_embeddings import LocalEmbeddings


def test_oversized_embedding_never_dispatches_or_silently_truncates():
    provider = LocalEmbeddings()
    model = Mock()
    model.tokenizer.encode.return_value = [1] * 513
    provider._model = model
    with pytest.raises(ValueError, match="exceeds 512 tokens"):
        provider.encode_batch(["oversized policy"])
    model.encode.assert_not_called()


@pytest.mark.parametrize("texts,kind", [([], "passage"), (["x"] * 17, "passage"), (["x"], "invalid")])
def test_invalid_batch_rejected_before_loading_model(texts, kind):
    provider = LocalEmbeddings()
    provider.load = Mock(side_effect=AssertionError("must not load"))
    with pytest.raises(ValueError, match="1–16"):
        provider.encode_batch(texts, kind)
    provider.load.assert_not_called()
