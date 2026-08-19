"""エージェント層の結線とレビュー判定の検証。

モデル呼び出しは行わない（AWS 認証情報なしで通ること）。
"""

from __future__ import annotations

import pytest

from src.agents.review_agent import _parse_verdict
from src.config import Settings


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("VERDICT: ok\n指摘なし", "ok"),
        ("verdict: OK", "ok"),
        ("VERDICT: revise\n- 出典が無い", "revise"),
        ("前置き\nVERDICT: revise", "revise"),
        # 判定行が読めない場合は revise に倒す。判定不能を「問題なし」にしない。
        ("よくわかりません", "revise"),
        ("", "revise"),
    ],
)
def test_parse_verdict(text: str, expected: str) -> None:
    assert _parse_verdict(text) == expected


def test_orchestrator_wires_agents_and_tools() -> None:
    """結線を固定する。

    構築時に boto3 クライアントは作られるが Bedrock API 呼び出しは発生しない
    （認証情報は conftest のダミーで足りる）。
    """
    from src.agents.orchestrator import ResearchOrchestrator

    orchestrator = ResearchOrchestrator(Settings(aws_region="ap-northeast-1"))
    assert orchestrator._agent.name == "OrchestratorAgent"
    # Orchestrator が持つツールは investigate (= SearchAgent) のみ
    tool_names = set(orchestrator._agent.tool_names)
    assert "investigate" in tool_names
    # ReviewAgent はツールとして渡さない（決定的に実行するため）
    assert not any("review" in n.lower() for n in tool_names)


def test_search_agent_exposes_web_search_tool() -> None:
    from src.agents.search_agent import build_search_agent

    agent = build_search_agent(Settings())
    assert "web_search" in set(agent.tool_names)
