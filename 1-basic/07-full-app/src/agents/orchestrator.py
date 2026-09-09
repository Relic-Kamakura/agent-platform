"""OrchestratorAgent: 調査依頼を観点に分解し、SearchAgent の結果を統合する。

モデル割り当ての理由:
    どの観点に分解するか、結果をどう統合するかは判断を伴う。
    ここの質が成果物の質を決めるため、上位モデル (MODEL_ID_ORCHESTRATOR) を割り当てている。

処理の流れ:
    1. Orchestrator が investigate ツール (= SearchAgent) を使って調査し、報告をまとめる
    2. ReviewAgent が報告を検証する（コードから決定的に 1 回実行）
    3. verdict が revise なら、指摘を渡して Orchestrator に 1 回だけ修正させる

3 の修正回数を 1 回に固定しているのは、ターン数とコストの上限を予測可能にするため。
修正しても直らない場合は、指摘を最終成果物に添えて返し、人が判断できるようにする。

Agent の寿命:
    Strands の Agent は会話履歴とメトリクスを持ち、同じインスタンスの並行実行を
    ConcurrencyException で拒否する。AgentCore Runtime は /invocations をスレッドプールで
    並列に処理するので、Agent はリクエスト（run() の呼び出し）ごとに作る。
    BedrockModel（boto3 クライアント）はスレッドセーフなので、プロセスで 1 つを共有する。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from strands import Agent
from strands.types.exceptions import MaxTokensReachedException

from ..config import Settings
from ..guards import Guards, build_guards
from ..observability import log_event
from .models import build_model
from .results import partial_text, result_text
from .review_agent import ReviewAgent, ReviewOutcome
from .search_agent import build_search_agent_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
あなたは競合リサーチの統括担当です。利用者の依頼を調査観点に分解し、investigate ツールで
観点ごとに調べ、結果を 1 つの報告にまとめます。

守ること:
- 依頼を 2〜4 個の調査観点に分解し、観点ごとに investigate を 1 回ずつ呼ぶ。
- investigate が返した事実だけを使う。自分の知識で補わない。
- 事実には出典 URL を残す。
- 確認できなかった観点は「確認できず」と明記する。
- ツール呼び出しの上限に達したという通知を受け取ったら、それ以上調べようとせず、
  手持ちの情報で報告をまとめる。

報告の構成:
1. 要約（3 行以内）
2. 観点ごとの調査結果（事実と出典 URL）
3. 確認できなかったこと
"""

TRUNCATED_NOTICE = "（出力がトークン上限に達したため、報告はここで打ち切られています）"


@dataclass
class ResearchReport:
    question: str
    report: str
    review: ReviewOutcome
    revised: bool = False
    truncated: bool = False
    tool_calls: int = 0
    usage: dict[str, int] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            "question": self.question,
            "report": self.report,
            "review": {"verdict": self.review.verdict, "notes": self.review.notes},
            "revised": self.revised,
            "truncated": self.truncated,
            "tool_calls": self.tool_calls,
            "usage": self.usage,
        }


class ResearchOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # モデルはプロセスで 1 つ。Agent は run() ごとに build_agent() で作る。
        self._orchestrator_model = build_model(settings, "orchestrator")
        self._search_model = build_model(settings, "search")
        self._reviewer = ReviewAgent(settings)

    def build_agent(self) -> tuple[Agent, Guards]:
        """1 リクエスト分の Orchestrator Agent とガード一式を作る。"""
        guards = build_guards(self._settings, role="orchestrator")
        agent = Agent(
            name="OrchestratorAgent",
            model=self._orchestrator_model,
            system_prompt=SYSTEM_PROMPT,
            tools=[build_search_agent_tool(self._settings, model=self._search_model)],
            hooks=guards.hooks,
            callback_handler=None,
        )
        return agent, guards

    def run(self, question: str, on_stage: Callable[[str], None] | None = None) -> ResearchReport:
        """調査を 1 回実行する。

        on_stage: 進捗ステージ ("research" / "review" / "revise") ごとに呼ばれる。
        ストリーミング応答が UI へ進捗を渡すために使う。
        """
        notify = on_stage or (lambda _stage: None)
        agent, guards = self.build_agent()

        notify("research")
        report, truncated = _invoke(agent, question)
        # ツール呼び出し回数は Agent の呼び出しごとに 0 に戻るので、ここで退避する
        tool_calls = guards.tool_limiter.total_calls

        notify("review")
        review = self._reviewer.review(question, report)
        revised = False

        if review.needs_revision:
            notify("revise")
            log_event(logger, logging.INFO, "revision_started")
            revision_prompt = (
                "以下は、あなたが作成した報告に対する検証担当からの指摘です。\n"
                f"{review.notes}\n\n"
                "指摘を反映した報告を出力してください。追加の調査は行わず、"
                "手持ちの情報の範囲で修正してください。"
            )
            report, truncated = _invoke(agent, revision_prompt)
            revised = True

        usage = guards.usage_logger.last_usage
        log_event(
            logger,
            logging.INFO,
            "research_completed",
            verdict=review.verdict,
            revised=revised,
            truncated=truncated,
            tool_calls=tool_calls,
            turns=guards.turn_limiter.turns,
        )
        return ResearchReport(
            question=question,
            report=report,
            review=review,
            revised=revised,
            truncated=truncated,
            tool_calls=tool_calls,
            usage=usage,
        )


def _invoke(agent: Agent, prompt: str) -> tuple[str, bool]:
    """Agent を 1 回呼び、本文と「出力上限で打ち切られたか」を返す。

    Strands は max_tokens に達すると MaxTokensReachedException を送出する。
    途中までの本文は agent.messages に残っているので、それを救出して報告に使う。
    黙って 500 にするより、途中までの内容と打ち切りの事実を返すほうが利用者は次の判断ができる。
    """
    try:
        return result_text(agent(prompt)), False
    except MaxTokensReachedException:
        log_event(logger, logging.WARNING, "max_tokens_reached", agent=agent.name)
        return f"{partial_text(agent)}\n\n{TRUNCATED_NOTICE}".strip(), True
