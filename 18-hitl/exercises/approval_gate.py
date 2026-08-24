"""ハンズオン 18.3: 取り消せない操作に人間の承認を挟むゲート。

TODO を実装し、`uv run 01_run_gate.py` で動かす。
実装が終わったら TODO コメントは消す。完成形は solutions/approval_gate.py。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from strands.hooks import BeforeToolCallEvent, HookRegistry

logger = logging.getLogger(__name__)


@dataclass
class ApprovalGate:
    """取り消せない操作に人間の承認を挟むゲート（HITL）。

    approver は注入式。CLI なら input() で人間に聞き、テストなら固定値を返し、
    本番なら Slack 承認フローに置き換える。ゲート本体を変えずに承認手段だけ
    差し替えられる。
    """

    requires_approval: set[str]
    approver: Callable[[str, dict], bool]

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        # TODO(1): BeforeToolCallEvent に self._check を登録する。
        #   登録は registry.add_callback(イベント型, コールバック)
        ...

    def _check(self, event: BeforeToolCallEvent) -> None:
        # TODO(2): ツール名を event.tool_use.get("name", "<unknown>") で取り、
        #   requires_approval に含まれないツールは何もせずに return する
        #   （読み取り系ツールで approver を呼ばない）
        # TODO(3): 含まれるツールは approver(ツール名, dict(event.tool_use.get("input", {})))
        #   で人間に尋ねる。結果は承認・否認のどちらでも logger.info で 1 行残す。
        #   否認されたら event.cancel_tool に理由の文字列を入れる。理由にはツール名と
        #   人間の承認が得られなかったことを含め、モデルが代替行動
        #   （実行せずに下書きを提示する等）に移れる文にする
        ...
