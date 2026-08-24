"""ハンズオン 19.3 の模範解答。exercises/review.py の完成形。"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Verdict(BaseModel):
    """レビュー判定。スキーマとしてモデルに渡す（提供済み・編集不要）。

    Field の description がモデルへの指示を兼ねるので、
    プロンプトに形式の説明を書く必要が無くなる。
    """

    verdict: Literal["approve", "revise"] = Field(
        description="修正が不要なら approve、1 つでも指摘があるなら revise"
    )
    reasons: list[str] = Field(description="判定の理由。指摘が無ければ空リスト")


def parse_verdict_text(text: str) -> Verdict:
    """テキスト応答の 1 行目から判定を読み取る（提供済み・編集不要）。

    「1 行目は必ず VERDICT: approve か VERDICT: revise」というプロンプト上の
    約束をあてにした、壊れやすい実装。約束が破られたときに何が起きるかを
    01_break_parser.py で観察する。
    """
    lines = [line for line in text.strip().splitlines() if line.strip()]
    first_line = lines[0] if lines else ""
    if first_line.upper().startswith("VERDICT:"):
        value = first_line.split(":", 1)[1].strip().lower()
        verdict = "approve" if value.startswith("approve") else "revise"
        return Verdict(verdict=verdict, reasons=[line.strip("- ") for line in lines[1:]])
    # 判定行を読めなかった。安全側に倒して revise 扱いにする
    return Verdict(verdict="revise", reasons=["判定行を読み取れなかったため要修正扱い"])


def structured_verdict(agent, report: str) -> Verdict:
    """agent に report を検証させ、判定を Verdict として受け取る。

    受け取るもの: agent（strands の Agent）と、検証対象の報告テキスト。
    返すもの: 検証済みの Verdict。判定を取得できなかった場合は revise の Verdict。
    """
    prompt = f"# 検証対象の報告\n{report}\n\n上記の報告を検証してください。"
    fallback = Verdict(verdict="revise", reasons=["検証結果を取得できなかったため要修正扱い"])
    try:
        result = agent(prompt, structured_output_model=Verdict)
    except Exception:
        # 判定不能を「問題なし」にしたら検証機構として意味をなさない。revise に倒す
        logger.warning("structured_output_failed report_chars=%s", len(report), exc_info=True)
        return fallback
    if result.structured_output is None:
        logger.warning("structured_output_missing report_chars=%s", len(report))
        return fallback
    return result.structured_output
