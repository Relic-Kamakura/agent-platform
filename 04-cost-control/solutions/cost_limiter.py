"""ハンズオン 4.3 の模範解答。exercises/cost_limiter.py の完成形。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from strands.hooks import BeforeInvocationEvent, BeforeModelCallEvent, HookRegistry

logger = logging.getLogger(__name__)


@dataclass
class CostLimiter:
    """入力トークンの積算上限。

    BeforeModelCallEvent.projected_input_tokens（次のモデル呼び出しの予測入力量）を
    積算し、上限を超えたら理由付きで中断する。回数ベースの上限を補完する
    「量」ベースのガード。
    """

    max_total_tokens: int
    _accumulated: int = field(default=0, init=False)

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(BeforeInvocationEvent, self._reset)
        registry.add_callback(BeforeModelCallEvent, self._check)

    def _reset(self, event: BeforeInvocationEvent) -> None:
        self._accumulated = 0

    def _check(self, event: BeforeModelCallEvent) -> None:
        projected = event.projected_input_tokens
        if projected is None:
            # 予測が取れないターンは加算しない。過剰に厳しく止めない
            return
        self._accumulated += int(projected)
        if self._accumulated > self.max_total_tokens:
            event.cancel = (
                f"入力トークンの概算上限 ({self.max_total_tokens}) に達したため中断しました。"
                "追加の調査はせず、ここまでの情報で結論をまとめてください。"
            )
            logger.warning(
                "cost_limit_exceeded limit=%s accumulated=%s",
                self.max_total_tokens,
                self._accumulated,
            )
