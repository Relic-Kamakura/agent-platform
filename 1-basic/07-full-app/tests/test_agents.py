"""エージェント層の結線とレビュー判定の検証。

モデル呼び出しは行わない（AWS 認証情報なしで通ること）。
"""

from __future__ import annotations

import pytest
from strands.agent.agent_result import AgentResult
from strands.telemetry.metrics import EventLoopMetrics
from strands.types.exceptions import MaxTokensReachedException

from src.agents.results import result_text
from src.agents.review_agent import ReviewAgent, _parse_verdict
from src.config import Settings


def _agent_result(text: str) -> AgentResult:
    """モデルを呼ばずに AgentResult を組む。Agent と後続処理の境界を検証するための材料。"""
    return AgentResult(
        stop_reason="end_turn",
        message={"role": "assistant", "content": [{"text": text}]},
        metrics=EventLoopMetrics(),
        state={},
    )


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
    agent, guards = orchestrator.build_agent()
    assert agent.name == "OrchestratorAgent"
    # Orchestrator が持つツールは investigate (= SearchAgent) のみ
    tool_names = set(agent.tool_names)
    assert "investigate" in tool_names
    # ReviewAgent はツールとして渡さない（決定的に実行するため）
    assert not any("review" in n.lower() for n in tool_names)
    # Agent はリクエストごとに別インスタンス。履歴と計測が混ざらないことの前提
    another, _ = orchestrator.build_agent()
    assert another is not agent
    assert guards.tool_limiter.total_calls == 0


def test_result_text_returns_body_not_dict_repr() -> None:
    """AgentResult から取るのは本文。str(result.message) は dict の文字列表現で本文ではない。"""
    result = _agent_result("VERDICT: ok\n指摘なし")
    assert result_text(result) == "VERDICT: ok\n指摘なし"
    assert str(result.message).startswith("{'role'")


def test_review_reads_verdict_from_message_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """Agent の応答を受け取る境界を通しても verdict が読めること。"""
    reviewer = ReviewAgent(Settings())
    monkeypatch.setattr(
        reviewer, "_build_agent", lambda: lambda _prompt: _agent_result("VERDICT: ok\n指摘なし")
    )
    outcome = reviewer.review("質問", "報告")
    assert outcome.verdict == "ok"
    assert outcome.notes == "VERDICT: ok\n指摘なし"


def test_run_rescues_partial_report_when_max_tokens_reached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """max_tokens 到達は例外で届く。途中までの本文を救出し、打ち切りを明示して返すこと。"""
    from src.agents.orchestrator import TRUNCATED_NOTICE, ResearchOrchestrator
    from src.agents.review_agent import ReviewOutcome
    from src.guards import build_guards

    settings = Settings()
    orchestrator = ResearchOrchestrator(settings)

    class TruncatingAgent:
        name = "OrchestratorAgent"

        def __init__(self) -> None:
            self.messages = [{"role": "assistant", "content": [{"text": "途中までの報告"}]}]

        def __call__(self, _prompt: str) -> AgentResult:
            raise MaxTokensReachedException("max_tokens reached")

    monkeypatch.setattr(
        orchestrator,
        "build_agent",
        lambda: (TruncatingAgent(), build_guards(settings, role="orchestrator")),
    )
    monkeypatch.setattr(
        orchestrator._reviewer,
        "review",
        lambda _q, _r: ReviewOutcome(verdict="ok", notes="指摘なし"),
    )

    report = orchestrator.run("質問")
    assert report.truncated is True
    assert report.report.startswith("途中までの報告")
    assert TRUNCATED_NOTICE in report.report
    assert report.to_payload()["truncated"] is True


def test_search_agent_exposes_web_search_tool() -> None:
    from src.agents.search_agent import build_search_agent

    agent = build_search_agent(Settings())
    assert "web_search" in set(agent.tool_names)
