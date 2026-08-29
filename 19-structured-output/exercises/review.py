"""ハンズオン 19.3: レビュー判定を構造化出力で受け取る。

TODO を実装し、`uv run pytest -q` で判定する。
実装が終わったら TODO コメントは消す。完成形は solutions/review.py。
"""

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
    形式の指示に頼った実装。形式が守られなかったときに何が起きるかを
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
    # TODO(1): agent を構造化出力付きで呼び出し、判定を返す。
    #   result = agent(prompt, structured_output_model=Verdict) と呼ぶと、
    #   検証済みの Verdict インスタンスが result.structured_output に入る
    # TODO(2): 失敗したときは revise の Verdict を返す。
    #   呼び出しが例外を投げた場合と result.structured_output が None の場合は、
    #   logger.warning で 1 行残したうえで、revise の Verdict
    #   （reasons に判定を取得できなかった旨）を返す。
    #   判定不能を「問題なし」にしたら検証機構として意味をなさない
    ...
