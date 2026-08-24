"""演習 18 の合格判定。承認・否認の両パスを検査する（完全オフライン）。"""

from __future__ import annotations

import pathlib

from strands.hooks import BeforeToolCallEvent, HookRegistry


def _fire(gate, tool_name: str, tool_input: dict) -> BeforeToolCallEvent:
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


def test_no_todo_left(approval_gate_cls) -> None:
    import approval_gate as mod

    source = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/approval_gate.py に TODO が残っています。README 18.3 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


def test_unlisted_tool_passes_without_asking(approval_gate_cls) -> None:
    asked: list[str] = []
    gate = approval_gate_cls(
        requires_approval={"send_email"},
        approver=lambda name, tool_input: asked.append(name) or True,
    )
    event = _fire(gate, "web_search", {"query": "x"})
    assert event.cancel_tool is False
    assert asked == [], (
        "承認対象外のツールで approver を呼ばないでください（README 18.2）。"
        "読み取り系ツールまで人間の応答待ちになります。"
    )


def test_approved_tool_runs(approval_gate_cls) -> None:
    gate = approval_gate_cls(requires_approval={"send_email"}, approver=lambda name, tool_input: True)
    event = _fire(gate, "send_email", {"to": "a@example.com"})
    assert event.cancel_tool is False, "承認されたツールはキャンセルしないでください。"


def test_denied_tool_is_cancelled_with_reason(approval_gate_cls) -> None:
    gate = approval_gate_cls(requires_approval={"send_email"}, approver=lambda name, tool_input: False)
    event = _fire(gate, "send_email", {"to": "a@example.com"})
    assert isinstance(event.cancel_tool, str), (
        "否認時は bool ではなく理由の文字列を cancel_tool に入れてください（第4章と同じ設計）。"
    )
    assert "send_email" in event.cancel_tool, "理由にツール名を含めてください。"
    assert "承認" in event.cancel_tool, "人間の承認が得られなかったことを理由に書いてください。"


def test_approver_receives_tool_input(approval_gate_cls) -> None:
    received: dict = {}
    gate = approval_gate_cls(
        requires_approval={"send_email"},
        approver=lambda name, tool_input: received.update(tool_input) or True,
    )
    _fire(gate, "send_email", {"to": "a@example.com", "subject": "hi"})
    assert received == {"to": "a@example.com", "subject": "hi"}, (
        "approver にはツールの入力を渡してください。人間は引数を見て判断します。"
    )
