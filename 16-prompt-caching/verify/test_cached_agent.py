"""演習 16 の合格判定。モデルは呼ばず、組み立ての配線だけを検査する。"""

from __future__ import annotations

import pathlib

import pytest
from strands import Agent


def _build(agent_module) -> Agent:
    agent = agent_module.build_cached_agent(
        model_id="dummy-model-id", region_name="us-east-1"
    )
    if not isinstance(agent, Agent):
        pytest.fail(
            "build_cached_agent が Agent を返していません。README 16.3.1 に沿って"
            "TODO(2) を実装してください。"
        )
    return agent


def test_no_todo_left(agent_module) -> None:
    source = pathlib.Path(agent_module.__file__).read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/cached_agent.py に TODO が残っています。README 16.3.1 に沿って"
        "実装し、終わったら TODO コメントを消してください。"
    )


def test_cache_config_wired(agent_module) -> None:
    agent = _build(agent_module)
    cache = agent.model.get_config().get("cache_config")
    assert cache is not None, (
        "BedrockModel に cache_config が渡っていません（16.3.1 TODO(1)）。"
    )
    assert getattr(cache, "strategy", None) == "auto", (
        "CacheConfig(strategy='auto') を渡してください（16.2）。"
    )


def test_model_uses_arguments(agent_module) -> None:
    agent = _build(agent_module)
    assert agent.model.get_config().get("model_id") == "dummy-model-id", (
        "model_id は引数の値をそのまま BedrockModel に渡してください（16.3.1 TODO(1)）。"
    )


def test_guide_passed_unchanged(agent_module) -> None:
    agent = _build(agent_module)
    assert agent.system_prompt == agent_module.RESEARCH_GUIDE, (
        "RESEARCH_GUIDE をそのまま system_prompt に渡してください。"
        "現在時刻などを足すと毎回先頭が変わり、すべてキャッシュミスになります（16.1.2）。"
    )
