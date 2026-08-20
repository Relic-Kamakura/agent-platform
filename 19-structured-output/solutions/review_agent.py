"""第19章の模範解答。07-full-app/src/agents/review_agent.py の完成形。

ReviewAgent: Orchestrator の出力を検証する。判定は構造化出力で受け取る。

モデル割り当ての理由:
    出典の欠落や、事実と推測の混在を見抜く必要がある。見逃しが成果物の信頼性に
    直結するため、上位モデル (MODEL_ID_REVIEW) を割り当てている。

呼び出し方の設計判断:
    ツールにせず orchestrator.py のコードから決定的に 1 回実行する（第5章）。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field
from strands import Agent

from ..config import Settings
from ..guards import build_guards
from ..observability import log_event
from .models import build_model

logger = logging.getLogger(__name__)

# 形式（VERDICT 行）はスキーマに移したので、プロンプトは検証観点だけを教える
SYSTEM_PROMPT = """\
あなたは競合リサーチ報告の検証担当です。渡された報告を読み、以下だけを確認します。

1. 事実として書かれている記述に出典 URL が付いているか
2. 元の調査依頼に対して、答えていない観点が残っていないか
3. 出典の内容から言えないことを断定していないか

報告そのものを書き直してはいけません。指摘だけを返します。
"""


class ReviewVerdict(BaseModel):
    """検証結果。スキーマがモデルに強制されるので、形式の言い換えは起きない。"""

    verdict: Literal["ok", "revise"] = Field(
        description="修正が不要なら ok、1 つでも指摘があるなら revise"
    )
    notes: str = Field(description="指摘の箇条書き。指摘が無ければ「指摘なし」と書く")


@dataclass(frozen=True)
class ReviewOutcome:
    verdict: str  # "ok" | "revise"
    notes: str

    @property
    def needs_revision(self) -> bool:
        return self.verdict == "revise"


def _outcome_from(verdict: ReviewVerdict | None) -> ReviewOutcome:
    """構造化結果を ReviewOutcome に変換する。

    None（構造化出力が得られなかった）は revise に倒す。
    判定不能を「問題なし」にしたら検証機構として意味をなさないため。
    """
    if verdict is None:
        return ReviewOutcome(verdict="revise", notes="検証結果を取得できなかったため要修正扱い")
    return ReviewOutcome(verdict=verdict.verdict, notes=verdict.notes)


class ReviewAgent:
    def __init__(self, settings: Settings) -> None:
        self._guards = build_guards(settings, role="review")
        self._agent = Agent(
            name="ReviewAgent",
            model=build_model(settings, "review"),
            system_prompt=SYSTEM_PROMPT,
            structured_output_model=ReviewVerdict,
            hooks=self._guards.hooks,
            callback_handler=None,
        )

    def review(self, question: str, report: str) -> ReviewOutcome:
        prompt = (
            f"# 元の調査依頼\n{question}\n\n"
            f"# 検証対象の報告\n{report}\n\n"
            "上記を検証してください。"
        )
        result = self._agent(prompt)
        outcome = _outcome_from(result.structured_output)
        log_event(logger, logging.INFO, "review_completed", verdict=outcome.verdict)
        return outcome
