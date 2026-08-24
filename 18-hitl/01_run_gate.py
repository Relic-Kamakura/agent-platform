"""ApprovalGate にイベントを手で流し、承認と否認で挙動が変わるのを見る（編集不要）。"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from strands.hooks import BeforeToolCallEvent, HookRegistry

from approval_gate import ApprovalGate


def fire(gate: ApprovalGate, tool_name: str, tool_input: dict) -> BeforeToolCallEvent:
    """ツール実行直前のイベントを手で作ってゲートに通す（第4章と同じ技法）。"""
    event = BeforeToolCallEvent(
        agent=None,
        selected_tool=None,
        tool_use={"name": tool_name, "toolUseId": "t1", "input": tool_input},
        invocation_state={},
    )
    registry = HookRegistry()
    gate.register_hooks(registry)
    registry.invoke_callbacks(event)
    return event


# ケース 1: 承認対象外のツール。approver は呼ばれないはず
asked: list[str] = []
gate = ApprovalGate(
    requires_approval={"send_email"},
    approver=lambda name, tool_input: asked.append(name) or True,
)
event = fire(gate, "web_search", {"query": "A社 シェア"})
print(f"web_search : cancel_tool={event.cancel_tool}  approver への問い合わせ={len(asked)} 回")

# ケース 2: 承認対象のツールを、常に承認する approver で通す
gate = ApprovalGate(requires_approval={"send_email"}, approver=lambda name, tool_input: True)
event = fire(gate, "send_email", {"to": "taro@example.com"})
print(f"send_email : cancel_tool={event.cancel_tool}  （承認されたので実行される）")

# ケース 3: 同じツールを、常に否認する approver で止める
gate = ApprovalGate(requires_approval={"send_email"}, approver=lambda name, tool_input: False)
event = fire(gate, "send_email", {"to": "taro@example.com"})
print("send_email : 否認。ツール結果としてモデルに渡る理由 ->")
print(f"  {event.cancel_tool}")
