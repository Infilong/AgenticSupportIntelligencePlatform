import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_mock_embeddings_do_not_require_price_or_key():
    assert Settings(_env_file=None, embedding_token_cost_per_1k="").embedding_provider == "mock"


@pytest.mark.parametrize("overrides", [
    {"openai_api_key": None}, {"embedding_token_cost_per_1k": None},
    {"embedding_token_cost_per_1k": 0}, {"embedding_dimensions": 1537},
    {"openai_timeout_seconds": 0},
])
def test_invalid_real_embedding_configuration_fails_at_startup(overrides):
    values = dict(embedding_provider="openai", openai_api_key="synthetic",
                  embedding_token_cost_per_1k=0.001)
    values.update(overrides)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)
