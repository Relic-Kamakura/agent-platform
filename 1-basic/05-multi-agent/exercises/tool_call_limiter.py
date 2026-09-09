"""ツール呼び出し回数の上限ガード（提供部品。編集不要）。

エージェントを新しく組むときは、この種のガードを必ず hooks に付ける。
ガードなしのエージェントは、モデルが呼び続ける限りコストが増え続ける。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from strands.hooks import BeforeInvocationEvent, BeforeToolCallEvent, HookRegistry

logger = logging.getLogger(__name__)


@dataclass
class ToolCallLimiter:
    """ツール呼び出しの総数上限。超えたら理由付きでツール実行を中断する。

    cancel_tool に理由の文字列を入れると、ツール結果の代わりにその理由がモデルへ渡る。
    モデルはループを続け、理由を読んで手持ちの情報で結論をまとめる方向に切り替わる。
    """

    max_calls: int
    _calls: int = field(default=0, init=False)

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(BeforeInvocationEvent, self._reset)
        registry.add_callback(BeforeToolCallEvent, self._check)

    def _reset(self, event: BeforeInvocationEvent) -> None:
        self._calls = 0

    def _check(self, event: BeforeToolCallEvent) -> None:
        self._calls += 1
        if self._calls > self.max_calls:
            event.cancel_tool = (
                f"ツール呼び出しの上限 ({self.max_calls} 回) に達しました。"
                "追加の呼び出しはせず、ここまでの情報で結論をまとめてください。"
            )
            logger.warning("tool_call_limit_exceeded limit=%s", self.max_calls)
