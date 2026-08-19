from __future__ import annotations

import pytest

from src.config import Settings, derive_inference_prefix
from src.errors import ConfigurationError


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("ap-northeast-1", "apac"),
        ("ap-southeast-2", "apac"),
        ("us-east-1", "us"),
        ("eu-west-1", "eu"),
        ("us-gov-east-1", "us-gov"),
    ],
)
def test_derive_inference_prefix(region: str, expected: str) -> None:
    assert derive_inference_prefix(region) == expected


def test_model_id_uses_derived_prefix() -> None:
    s = Settings(aws_region="ap-northeast-1", model_id_orchestrator="anthropic.claude-x")
    assert s.model_id_for("orchestrator") == "apac.anthropic.claude-x"


def test_empty_prefix_disables_inference_profile() -> None:
    s = Settings(bedrock_model_id_prefix="", model_id_search="anthropic.claude-y")
    assert s.model_id_for("search") == "anthropic.claude-y"


def test_full_override_wins() -> None:
    s = Settings(model_id_review_full="global.anthropic.claude-z")
    assert s.model_id_for("review") == "global.anthropic.claude-z"


def test_prefix_with_trailing_dot_is_normalised() -> None:
    s = Settings(bedrock_model_id_prefix="us.", model_id_search="anthropic.claude-y")
    assert s.model_id_for("search") == "us.anthropic.claude-y"


def test_tavily_without_key_is_rejected() -> None:
    with pytest.raises(ConfigurationError):
        Settings(search_provider="tavily", tavily_api_key=None)


def test_bad_region_is_rejected() -> None:
    with pytest.raises(ConfigurationError):
        Settings(aws_region="tokyo")


def test_unknown_prefix_produces_warning() -> None:
    assert Settings(bedrock_model_id_prefix="xx").prefix_warning() is not None
    assert Settings(aws_region="ap-northeast-1").prefix_warning() is None


def test_describe_models_covers_all_roles() -> None:
    assert set(Settings().describe_models()) == {"orchestrator", "search", "review"}
