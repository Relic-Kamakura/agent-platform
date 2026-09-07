"""演習 04 の合格判定。イベントを手で作って hook を検証する（第6章で再登場する技法）。"""

from __future__ import annotations

import pathlib

from strands.hooks import BeforeInvocationEvent, BeforeModelCallEvent, HookRegistry


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
    registry = HookRegistry()
    limiter.register_hooks(registry)
    registry.invoke_callbacks(event)


def test_no_todo_left(cost_limiter_cls) -> None:
    import cost_limiter as mod

    source = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/cost_limiter.py に TODO が残っています。README 4.3 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


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
