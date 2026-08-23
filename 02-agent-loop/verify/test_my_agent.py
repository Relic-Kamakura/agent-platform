"""第2章の合格判定。exercises/ のエージェントの構造を検査する（LLM は呼ばない）。"""

from __future__ import annotations

import os
import pathlib

import pytest

EXERCISES = pathlib.Path(__file__).resolve().parents[1] / "exercises"


def _completed_source(name: str, section: str) -> str:
    path = EXERCISES / f"{name}.py"
    assert path.exists(), f"exercises/{name}.py がありません。README {section} を読み直してください。"
    source = path.read_text(encoding="utf-8")
    assert "TODO" not in source, (
        f"exercises/{name}.py に TODO が残っています。README {section} に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )
    return source


def _import(name: str, section: str):
    _completed_source(name, section)
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
    from importlib import import_module

    try:
        return import_module(name)
    except ModuleNotFoundError:
        pytest.fail(f"exercises/{name}.py を import できません。README {section} を確認してください。")


def test_01_agent_has_now_tool() -> None:
    mod = _import("01_agent", "2.3")
    agent = getattr(mod, "agent", None)
    assert hasattr(agent, "tool_names"), "01_agent.py の agent = ... を Agent(...) に実装してください（2.3）。"
    assert "now" in set(agent.tool_names), "agent の tools に now を渡してください（2.3）。"


def test_01_agent_docstring_sections() -> None:
    mod = _import("01_agent", "2.3")
    fn = getattr(mod.now, "__wrapped__", mod.now)
    doc = fn.__doc__ or ""
    for section in ("受け取るもの", "返すもの", "含まないもの"):
        assert section in doc, (
            f"now の docstring に「{section}」がありません。"
            "3 節はモデルに渡る仕様書なので消さずに残してください（2.2 参照）。"
        )


def test_02_has_both_tools() -> None:
    mod = _import("02_add_tool", "2.5")
    agent = getattr(mod, "agent", None)
    assert hasattr(agent, "tool_names"), "02_add_tool.py の agent = ... を Agent(...) に実装してください（2.5）。"
    names = set(agent.tool_names)
    assert {"now", "char_count"} <= names, (
        f"agent の tools に now と char_count の両方を渡してください（2.5）。現在: {names}"
    )


def test_02_char_count_contract() -> None:
    mod = _import("02_add_tool", "2.5")
    fn = getattr(mod.char_count, "__wrapped__", mod.char_count)
    doc = fn.__doc__ or ""
    for section in ("受け取るもの", "返すもの", "含まないもの"):
        assert section in doc, f"char_count の docstring に「{section}」がありません（2.5 要件 2）。"
    assert "7" in str(fn(text="こんにちは世界")), "char_count('こんにちは世界') は 7 を含む文字列を返すはずです。"


def test_02_model_id_not_hardcoded() -> None:
    source = _completed_source("02_add_tool", "2.5")
    assert "environ" in source, (
        "モデル ID は環境変数から取ってください（既定値つきで可）。直書きはこのリポジトリの規約違反です。"
    )


def test_03_metrics_script() -> None:
    source = _completed_source("03_metrics", "2.6")
    assert "cycle_count" in source and "accumulated_usage" in source, (
        "03_metrics.py で cycle_count と accumulated_usage の両方を表示してください（2.6）。"
    )
