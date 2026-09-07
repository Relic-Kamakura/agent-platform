"""ReviewAgent: Orchestrator の出力を検証する。

モデル割り当ての理由:
    出典の欠落や、事実と推測の混在を見抜く必要がある。見逃しが成果物の信頼性に
    直結するため、上位モデル (MODEL_ID_REVIEW) を割り当てている。

呼び出し方の設計判断:
    このエージェントはツールとして Orchestrator に渡していない。
    ツールにすると「呼ぶかどうか」がモデルの裁量になり、検証がスキップされ得るため、
    orchestrator.py のコードから決定的に 1 回実行する。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from strands import Agent

from ..config import Settings
from ..guards import build_guards
from ..observability import log_event
from .models import build_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
あなたは競合リサーチ報告の検証担当です。渡された報告を読み、以下だけを確認します。

1. 事実として書かれている記述に出典 URL が付いているか
2. 元の調査依頼に対して、答えていない観点が残っていないか
3. 出典の内容から言えないことを断定していないか

出力形式（1 行目は必ずこの形式にすること）:
VERDICT: ok        <- 修正が不要な場合
VERDICT: revise    <- 修正が必要な場合

2 行目以降に、指摘を箇条書きで書きます。指摘が無ければ「指摘なし」と書きます。
報告そのものを書き直してはいけません。指摘だけを返します。
"""


@dataclass(frozen=True)
class ReviewOutcome:
    verdict: str  # "ok" | "revise"
    notes: str

    @property
    def needs_revision(self) -> bool:
        return self.verdict == "revise"


class ReviewAgent:
    def __init__(self, settings: Settings) -> None:
        self._guards = build_guards(settings, role="review")
        self._agent = Agent(
            name="ReviewAgent",
            model=build_model(settings, "review"),
            system_prompt=SYSTEM_PROMPT,
            hooks=self._guards.hooks,
            callback_handler=None,
        )

    def review(self, question: str, report: str) -> ReviewOutcome:
        prompt = (
            f"# 元の調査依頼\n{question}\n\n# 検証対象の報告\n{report}\n\n上記を検証してください。"
        )
        text = str(self._agent(prompt).message).strip()
        verdict = _parse_verdict(text)
        log_event(logger, logging.INFO, "review_completed", verdict=verdict)
        return ReviewOutcome(verdict=verdict, notes=text)


def _parse_verdict(text: str) -> str:
    """1 行目の 'VERDICT: ...' を読む。

    読めなかった場合は 'revise' 扱いにする。判定不能を「問題なし」に倒すと
    検証機構として意味をなさないため。
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("VERDICT:"):
            value = stripped.split(":", 1)[1].strip().lower()
            return "ok" if value.startswith("ok") else "revise"
    return "revise"
