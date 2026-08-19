"""第17章の合格判定。承認・否認の両パスを検査する（完全オフライン）。"""

from __future__ import annotations

import pytest
from strands.hooks import BeforeToolCallEvent, HookRegistry

try:
    from src.guards import ApprovalGate
except ImportError:
    pytest.fail(
        "src/guards.py に ApprovalGate がまだありません。README の 17.3 に沿って実装してください。",
        pytrace=False,
    )


def _fire(gate: ApprovalGate, tool_name: str, tool_input: dict) -> BeforeToolCallEvent:
    event = BeforeToolCallEvent(
        agent=None,  # type: ignore[arg-type]
        selected_tool=None,
        tool_use={"name": tool_name, "toolUseId": "t1", "input": tool_input},  # type: ignore[arg-type]
        invocation_state={},
    )
    registry = HookRegistry()
    gate.register_hooks(registry)
    registry.invoke_callbacks(event)
    return event


def test_unlisted_tool_passes_without_asking() -> None:
    asked = []
    gate = ApprovalGate(requires_approval={"send_email"}, approver=lambda n, i: asked.append(n) or True)
    event = _fire(gate, "web_search", {"query": "x"})
    assert event.cancel_tool is False
    assert asked == [], "承認対象外のツールで approver を呼ばないでください（17.3 要件 2）。"


def test_approved_tool_runs() -> None:
    gate = ApprovalGate(requires_approval={"send_email"}, approver=lambda n, i: True)
    event = _fire(gate, "send_email", {"to": "a@example.com"})
    assert event.cancel_tool is False, "承認されたツールはキャンセルしないでください。"


def test_denied_tool_is_cancelled_with_reason() -> None:
    gate = ApprovalGate(requires_approval={"send_email"}, approver=lambda n, i: False)
    event = _fire(gate, "send_email", {"to": "a@example.com"})
    assert isinstance(event.cancel_tool, str), (
        "否認時は bool ではなく理由の文字列を cancel_tool に入れてください（第4章と同じ設計）。"
    )
    assert "send_email" in event.cancel_tool, "理由にツール名を含めてください（17.3 要件 4）。"
    assert "承認" in event.cancel_tool, "人間の承認が得られなかったことを理由に書いてください。"


def test_approver_receives_tool_input() -> None:
    received = {}
    gate = ApprovalGate(
        requires_approval={"send_email"},
        approver=lambda n, i: received.update(i) or True,
    )
    _fire(gate, "send_email", {"to": "a@example.com", "subject": "hi"})
    assert received == {"to": "a@example.com", "subject": "hi"}, (
        "approver にはツールの入力を渡してください。人間は引数を見て判断します（17.3 要件 3）。"
    )
