"""AgentResult から本文を取り出す。

`str(result.message)` は Python の dict 表現（`{'role': 'assistant', ...}`）を返し、
本文ではない。本文は `str(result)`（AgentResult.__str__ がテキストブロックを連結する）で取る。
この差を 1 か所に閉じ込めるためのモジュール。
"""

from __future__ import annotations

from strands import Agent
from strands.agent.agent_result import AgentResult


def result_text(result: AgentResult) -> str:
    """モデル応答の本文だけを返す。"""
    return str(result).strip()


def partial_text(agent: Agent) -> str:
    """出力がトークン上限で打ち切られたときに、途中まで生成された本文を返す。

    Strands は MaxTokensReachedException を送出する前に、途中までのメッセージを
    agent.messages の末尾へ追加している。そこからテキストブロックだけを集める。
    """
    for message in reversed(agent.messages):
        if message.get("role") != "assistant":
            continue
        texts = [block["text"] for block in message.get("content", []) if "text" in block]
        if texts:
            return "".join(texts).strip()
    return ""
