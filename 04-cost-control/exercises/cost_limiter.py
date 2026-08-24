"""ハンズオン 4.3: トークン量で止めるガード。

TODO を実装し、`uv run 01_fire_events.py` で動かす。
実装が終わったら TODO コメントは消す。完成形は solutions/cost_limiter.py。
"""

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
        # TODO(1): 2 つのイベントにコールバックを登録する。
        #   - BeforeInvocationEvent に self._reset（リクエスト開始で積算を戻す）
        #   - BeforeModelCallEvent に self._check（モデル呼び出し直前に積算と判定）
        #   登録は registry.add_callback(イベント型, コールバック)
        ...

    def _reset(self, event: BeforeInvocationEvent) -> None:
        # TODO(2): 積算を 0 に戻す。インスタンスはリクエストを跨いで使い回されるため、
        #   リセットしないと前のリクエストの消費が残る
        ...

    def _check(self, event: BeforeModelCallEvent) -> None:
        # TODO(3): 積算と判定を実装する。
        #   - event.projected_input_tokens が None のときは加算しない（過剰に厳しく止めない）
        #   - 積算が max_total_tokens を超えたら、event.cancel に理由の文字列を入れる。
        #     理由には上限値と「ここまでの情報で結論をまとめる」という次の行動を含める
        #   - 止めたときは logger.warning でログを 1 行出す
        ...
