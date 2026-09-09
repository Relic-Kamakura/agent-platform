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
    agent = specialist_module.build_specialist_agent(specialist_module.build_model())
    assert agent is not None, _NOT_ASSEMBLED
    assert "lookup_pricing" in agent.tool_names, (
        "専門エージェントの tools に lookup_pricing を持たせてください。"
        "ツールが無いと、価格を推測で埋めた表が返ってきます。"
    )


def test_specialist_agent_has_guard(specialist_module) -> None:
    agent = specialist_module.build_specialist_agent(specialist_module.build_model())
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
        "hooks に ToolCallLimiter が付いていません。ガードなしのエージェントを新設しないでください。"
    )


def test_agent_is_created_per_call(specialist_module, monkeypatch) -> None:
    """Agent は compare_pricing の呼び出しごとに作ること（5.2.2）。

    Strands の Agent は同一インスタンスの並行実行を ConcurrencyException で拒否し、
    会話履歴も呼び出し間で残る。ツール関数の外で 1 つ作って使い回すと両方が問題になる。
    """
    created: list[object] = []

    class _FakeAgent:
        def __call__(self, prompt: str) -> str:
            return "| 企業 | プラン |"

    def _fake_build(model: object) -> _FakeAgent:
        created.append(model)
        return _FakeAgent()

    monkeypatch.setattr(specialist_module, "build_specialist_agent", _fake_build)
    tool = specialist_module.build_specialist_tool()
    fn = getattr(tool, "__wrapped__", tool)
    fn(companies="Acme Analytics, Globex Insights")
    fn(companies="Initech Data, Globex Insights")

    assert len(created) == 2, (
        "compare_pricing の呼び出しごとに build_specialist_agent(model) で Agent を作ってください"
        f"（作られた回数: {len(created)}）。ツール関数の外で作ると使い回しになります（5.2.2）。"
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
            f"compare_pricing の docstring に「{section}」の節がありません（docstring の 3 節構成。5.2.2）。"
        )
    assert "機能" in doc or "評判" in doc, (
        "「含まないもの」に価格以外（機能や評判）を調べないことを明記してください。"
        "これが無いと、オーケストレータはどの依頼をこのツールに委任すべきか迷います。"
    )
