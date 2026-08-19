"""第17章の模範解答。src/guards.py に追加するクラス（断片）。

guards.py 内では既存の import（logging / dataclass / hooks / log_event）を使う。
Callable は typing ではなく collections.abc から import する。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from strands.hooks import BeforeToolCallEvent, HookRegistry

from .observability import log_event  # guards.py 内では既存 import を使う

logger = logging.getLogger(__name__)


@dataclass
class ApprovalGate:
    """取り消せない操作に人間の承認を挟むゲート（HITL）。

    approver は注入式: CLI なら input()、テストなら固定値、本番なら Slack 承認フロー。
    ゲートの実装を変えずに承認手段だけ差し替えられる。
    """

    requires_approval: set[str]
    approver: Callable[[str, dict], bool]

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(BeforeToolCallEvent, self._check)

    def _check(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use.get("name", "<unknown>")
        if name not in self.requires_approval:
            # 読み取り系ツールを遅くしない。承認対象だけ人間に回す
            return

        tool_input = event.tool_use.get("input", {})
        approved = self.approver(name, dict(tool_input))
        log_event(
            logger,
            logging.INFO,
            "approval_requested",
            tool=name,
            approved=approved,
        )
        if not approved:
            event.cancel_tool = (
                f"ツール '{name}' の実行に人間の承認が得られませんでした。"
                "実行せずに、代わりに実行内容の下書きを提示してください。"
            )
