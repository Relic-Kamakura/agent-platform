"""演習 04 の合格判定。"""

from __future__ import annotations

import pytest
from strands.hooks import BeforeInvocationEvent, BeforeModelCallEvent


def _model_event(projected: int | None) -> BeforeModelCallEvent:
    return BeforeModelCallEvent(
        agent=None,  # type: ignore[arg-type]
        invocation_state={},
        projected_input_tokens=projected,
    )


def _invocation_event() -> BeforeInvocationEvent:
    return BeforeInvocationEvent(agent=None, invocation_state={})  # type: ignore[arg-type]


def _check(limiter, event) -> None:
    """登録されたコールバックを HookRegistry 経由で呼ぶ。"""
    from strands.hooks import HookRegistry

    registry = HookRegistry()
    limiter.register_hooks(registry)
    registry.invoke_callbacks(event)


def test_under_limit_does_not_cancel(cost_limiter_cls) -> None:
    limiter = cost_limiter_cls(max_total_tokens=10_000)
    event = _model_event(projected=4_000)
    _check(limiter, event)
    assert event.cancel is False


def test_exceeding_limit_cancels_with_reason(cost_limiter_cls) -> None:
    limiter = cost_limiter_cls(max_total_tokens=10_000)
    _check(limiter, _model_event(projected=6_000))
    blocked = _model_event(projected=6_000)
    _check(limiter, blocked)
    assert isinstance(blocked.cancel, str), (
        "bool ではなく理由の文字列を event.cancel に入れてください。"
        "モデルに『なぜ止まったか』が伝わりません。"
    )
    assert "10000" in blocked.cancel.replace(",", "").replace("_", ""), (
        "中断理由に上限値を含めてください。"
    )


def test_none_projection_is_ignored(cost_limiter_cls) -> None:
    limiter = cost_limiter_cls(max_total_tokens=1_000)
    for _ in range(5):
        event = _model_event(projected=None)
        _check(limiter, event)
        assert event.cancel is False, "projected_input_tokens が None のときは加算しないでください。"


def test_counter_resets_between_invocations(cost_limiter_cls) -> None:
    limiter = cost_limiter_cls(max_total_tokens=10_000)
    _check(limiter, _model_event(projected=9_000))
    _check(limiter, _invocation_event())  # 新しいリクエスト
    event = _model_event(projected=9_000)
    _check(limiter, event)
    assert event.cancel is False, (
        "BeforeInvocationEvent で積算をリセットしてください。"
        "インスタンスはリクエストを跨いで使い回されます。"
    )


def test_settings_and_guards_wiring() -> None:
    from src.config import Settings
    from src.guards import build_guards

    settings = Settings()
    assert hasattr(settings, "max_total_input_tokens"), (
        "Settings に max_total_input_tokens を追加してください。"
    )
    with pytest.raises(Exception):
        Settings(max_total_input_tokens=10)  # ge=1000 のバリデーション

    guards = build_guards(settings, role="test")
    assert hasattr(guards, "cost_limiter"), "Guards に cost_limiter を追加してください。"
    assert guards.cost_limiter in guards.hooks, "Guards.hooks に cost_limiter を含めてください。"


def test_config_default_has_rationale_comment() -> None:
    import os
    import pathlib

    app_dir = pathlib.Path(
        os.environ.get(
            "AGENT_APP_DIR", pathlib.Path(__file__).resolve().parents[2] / "07-full-app"
        )
    )
    config_src = (app_dir / "src/config.py").read_text(encoding="utf-8")
    idx = config_src.find("max_total_input_tokens")
    assert idx != -1
    # フィールド定義の前後 400 文字にコメントがあるか（根拠を書く習慣の判定）
    window = config_src[max(0, idx - 400) : idx + 200]
    assert "#" in window, (
        "max_total_input_tokens の既定値に根拠コメントを書いてください（このリポジトリの規約）。"
    )
