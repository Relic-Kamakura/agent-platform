"""演習 05 の合格判定。モデルは呼ばず、ツール化の構造と規約を検査する。"""

from __future__ import annotations

import pathlib

from strands.hooks import BeforeToolCallEvent

_NOT_ASSEMBLED = (
    "build_specialist_agent が Agent を返していません。README 5.3.1 の TODO(1) に沿って"
    "組み立ててください。"
)


def test_no_todo_left(specialist_module) -> None:
    source = pathlib.Path(specialist_module.__file__).read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/specialist.py に TODO が残っています。README 5.3 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


def test_specialist_agent_is_assembled(specialist_module) -> None:
    agent = specialist_module.build_specialist_agent()
    assert agent is not None, _NOT_ASSEMBLED
    assert "lookup_pricing" in agent.tool_names, (
        "専門エージェントの tools に lookup_pricing を持たせてください。"
        "ツールが無いと、価格を推測で埋めた表が返ってきます。"
    )


def test_specialist_agent_has_guard(specialist_module) -> None:
    agent = specialist_module.build_specialist_agent()
    assert agent is not None, _NOT_ASSEMBLED
    # ツール呼び出し直前イベントを上限より多く流し、どこかで中断されることを確かめる
    cancelled = False
    for i in range(10):
        event = BeforeToolCallEvent(
            agent=agent,
            selected_tool=None,
            tool_use={"input": {}, "name": "lookup_pricing", "toolUseId": f"t{i}"},
            invocation_state={},
        )
        agent.hooks.invoke_callbacks(event)
        if event.cancel_tool:
            cancelled = True
            break
    assert cancelled, (
        "hooks に ToolCallLimiter が付いていません。"
        "ガードなしのエージェントを新設しないでください（第4章）。"
    )


def test_wrapped_as_tool(specialist_module) -> None:
    tool = specialist_module.build_specialist_tool()
    assert hasattr(tool, "tool_spec"), (
        "build_specialist_tool の返り値がツールになっていません。"
        "compare_pricing に @tool を付けて、それを返してください。"
    )
    assert tool.tool_name == "compare_pricing", "ツール名は compare_pricing にしてください。"


def test_docstring_follows_convention(specialist_module) -> None:
    tool = specialist_module.build_specialist_tool()
    doc = tool.tool_spec["description"]
    for section in ("受け取るもの", "返すもの", "含まないもの"):
        assert section in doc, (
            f"compare_pricing の docstring に「{section}」の節がありません（第3章の規約）。"
        )
    assert "機能" in doc or "評判" in doc, (
        "「含まないもの」に価格以外（機能や評判）を調べないことを明記してください。"
        "これが無いと、オーケストレータはどの依頼をこのツールに委任すべきか迷います。"
    )
