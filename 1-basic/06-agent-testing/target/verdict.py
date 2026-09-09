"""ReviewAgent の応答から判定を読み取る（編集不要）。

Agent の応答を受け取る境界。`str(result.message)` は Python の dict 表現
（`{'role': 'assistant', ...}`）を返すので本文ではない。本文は `str(result)` で取る
（`AgentResult.__str__` がテキストブロックを連結する）。
"""

from __future__ import annotations

from strands.agent.agent_result import AgentResult


def parse_verdict(result: AgentResult) -> str:
    """応答本文の VERDICT 行を読み、"ok" か "revise" を返す。

    判定行が見つからないときは revise 扱いにする。
    パースに失敗しただけで、検証されないまま報告が通ることを防ぐため。
    """
    for line in str(result).splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("verdict:"):
            value = stripped.split(":", 1)[1].strip().lower()
            return "ok" if value == "ok" else "revise"
    return "revise"
