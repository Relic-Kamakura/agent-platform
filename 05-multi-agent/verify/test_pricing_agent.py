"""演習 05 の合格判定。LLM は呼ばず、結線と規約を検査する。"""

from __future__ import annotations

import os
import pathlib

from src.config import Settings


def _app_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("AGENT_APP_DIR", pathlib.Path(__file__).resolve().parents[2] / "07-full-app")
    )


def test_tool_exists_with_correct_name(pricing_module) -> None:
    tool = pricing_module.build_pricing_agent_tool(Settings())
    fn = getattr(tool, "__wrapped__", tool)
    assert fn.__name__ == "compare_pricing", "ツール名は compare_pricing にしてください。"


def test_docstring_follows_convention(pricing_module) -> None:
    tool = pricing_module.build_pricing_agent_tool(Settings())
    fn = getattr(tool, "__wrapped__", tool)
    doc = fn.__doc__ or ""
    for section in ("受け取るもの", "返すもの", "含まないもの"):
        assert section in doc, f"docstring に「{section}」の節がありません（03 章の規約）。"
    assert "機能" in doc or "評判" in doc, (
        "「含まないもの」に価格以外（機能・評判）を調べないことを明記してください。"
    )


def test_uses_lightweight_model_with_rationale(pricing_module) -> None:
    source = (_app_dir() / "src/agents/pricing_agent.py").read_text(encoding="utf-8")
    assert '"search"' in source or "'search'" in source, (
        "モデルは search ロール（軽量モデル）を使ってください。"
        "表への整形は定型処理であり、上位モデルはコストの無駄です。"
    )
    assert "build_guards" in source, "ガードなしのエージェントを作らないでください（04 章）。"


def test_orchestrator_has_pricing_tool() -> None:
    from src.agents.orchestrator import ResearchOrchestrator

    orchestrator = ResearchOrchestrator(Settings())
    tool_names = set(orchestrator._agent.tool_names)
    assert "compare_pricing" in tool_names, (
        "Orchestrator の tools に compare_pricing を追加してください。"
    )
    assert "investigate" in tool_names, "既存の investigate を消さないでください。"


def test_review_agent_is_still_deterministic() -> None:
    from src.agents.orchestrator import ResearchOrchestrator

    orchestrator = ResearchOrchestrator(Settings())
    tool_names = set(orchestrator._agent.tool_names)
    assert not any("review" in n.lower() for n in tool_names), (
        "ReviewAgent をツールにしないでください。検証は決定的実行のままにします（05 章 README）。"
    )
