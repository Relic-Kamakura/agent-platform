"""上限ガードの検証。

ガードはコスト事故を防ぐ機構なので、上限を超えたら確実に止まることをテストで固定する。
"""

from __future__ import annotations

from strands.hooks import BeforeInvocationEvent, BeforeModelCallEvent, BeforeToolCallEvent

from src.config import Settings
from src.guards import build_guards


def _tool_event(name: str) -> BeforeToolCallEvent:
    return BeforeToolCallEvent(
        agent=None,  # type: ignore[arg-type]
        selected_tool=None,
        tool_use={"name": name, "toolUseId": "t1", "input": {}},  # type: ignore[arg-type]
        invocation_state={},
    )


def _model_event() -> BeforeModelCallEvent:
    return BeforeModelCallEvent(agent=None, invocation_state={})  # type: ignore[arg-type]


def _invocation_event() -> BeforeInvocationEvent:
    return BeforeInvocationEvent(agent=None, invocation_state={})  # type: ignore[arg-type]


def test_total_tool_call_limit_cancels_with_reason() -> None:
    limiter = build_guards(Settings(max_tool_calls_total=2), "test").tool_limiter

    for _ in range(2):
        event = _tool_event("web_search")
        limiter._check(event)
        assert event.cancel_tool is False

    blocked = _tool_event("web_search")
    limiter._check(blocked)
    assert isinstance(blocked.cancel_tool, str)
    assert "上限" in blocked.cancel_tool
    assert limiter.total_calls == 2


def test_per_tool_limit_is_independent_of_total() -> None:
    limiter = build_guards(
        Settings(max_tool_calls_total=10, max_tool_calls_per_tool=1), "test"
    ).tool_limiter

    first = _tool_event("investigate")
    limiter._check(first)
    assert first.cancel_tool is False

    second = _tool_event("investigate")
    limiter._check(second)
    assert isinstance(second.cancel_tool, str)

    other = _tool_event("web_search")
    limiter._check(other)
    assert other.cancel_tool is False


def test_counters_reset_between_invocations() -> None:
    limiter = build_guards(Settings(max_tool_calls_total=1), "test").tool_limiter
    limiter._check(_tool_event("a"))
    assert limiter.total_calls == 1

    limiter._reset(_invocation_event())
    assert limiter.total_calls == 0

    event = _tool_event("a")
    limiter._check(event)
    assert event.cancel_tool is False


def test_turn_limit_cancels_model_call() -> None:
    turn_limiter = build_guards(Settings(max_agent_turns=2), "test").turn_limiter

    for _ in range(2):
        event = _model_event()
        turn_limiter._check(event)
        assert event.cancel is False

    blocked = _model_event()
    turn_limiter._check(blocked)
    assert isinstance(blocked.cancel, str)
    assert turn_limiter.turns == 3
