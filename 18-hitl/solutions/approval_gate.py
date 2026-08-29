"""ハンズオン 18.3 の模範解答。exercises/approval_gate.py の完成形。"""

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
        registry.add_callback(BeforeToolCallEvent, self._check)

    def _check(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use.get("name", "<unknown>")
        if name not in self.requires_approval:
            # 読み取り系ツールを遅くしない。承認対象だけ人間に尋ねる
            return

        tool_input = dict(event.tool_use.get("input", {}))
        approved = self.approver(name, tool_input)
        # どの操作が承認・否認されたかを後から追う監査ログの元データになる
        logger.info("approval_requested tool=%s approved=%s", name, approved)
        if not approved:
            event.cancel_tool = (
                f"ツール '{name}' の実行に人間の承認が得られませんでした。"
                "実行せずに、代わりに実行内容の下書きを提示してください。"
            )
