"""第16章の合格判定。設定とモデル生成の配線を検査する。"""

from __future__ import annotations

import os
import pathlib

import pytest

from src.config import Settings


def _app_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("AGENT_APP_DIR", pathlib.Path(__file__).resolve().parents[2] / "07-full-app")
    )


def test_setting_exists_with_rationale() -> None:
    settings = Settings()
    if not hasattr(settings, "enable_prompt_cache"):
        pytest.fail("Settings に enable_prompt_cache を追加してください（16.3 要件 1）。")
    assert settings.enable_prompt_cache is False, "既定は False にしてください（16.3 要件 1）。"

    config_src = (_app_dir() / "src/config.py").read_text(encoding="utf-8")
    idx = config_src.find("enable_prompt_cache")
    window = config_src[max(0, idx - 400) : idx + 100]
    assert "#" in window, "既定値の根拠コメントを書いてください（このリポジトリの規約）。"


def test_cache_config_wired_when_enabled() -> None:
    from src.agents.models import build_model

    model = build_model(Settings(enable_prompt_cache=True), "search")
    cache = model.get_config().get("cache_config")
    assert cache is not None, (
        "enable_prompt_cache=True のとき BedrockModel に cache_config が渡っていません（16.3 要件 2）。"
    )
    assert getattr(cache, "strategy", None) == "auto", "CacheConfig(strategy='auto') を使ってください。"


def test_cache_off_by_default() -> None:
    from src.agents.models import build_model

    model = build_model(Settings(), "search")
    assert model.get_config().get("cache_config") is None, (
        "無効時は cache_config を渡さないでください（設定で切り替え可能に）。"
    )
