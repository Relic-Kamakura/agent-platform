"""コスト・暴走対策の hook。

3 つを提供する。
- ToolCallLimiter: ツール呼び出し回数の上限（総数 / ツール別）
- TurnLimiter:     モデル呼び出し回数（エージェントのターン数）の上限
- UsageLogger:     1 リクエストあたりのトークン消費をログに出す

いずれも「止める」だけでなく「なぜ止まったか」をエージェントに伝える。
Strands の cancel_tool / cancel は str を代入すると、その文字列が中断理由として使われる。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from strands.hooks import (
    AfterInvocationEvent,
    BeforeInvocationEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
    HookCallback,
    HookProvider,
    HookRegistry,
)

from .config import Settings
from .observability import log_event

logger = logging.getLogger(__name__)


@dataclass
class ToolCallLimiter(HookProvider):
    """ツール呼び出し回数の上限。

    上限に達したツール呼び出しは実行せず、理由をエージェントに返す。
    エージェントは「これ以上調べられない」と理解して手持ちの情報でまとめられる。
    """

    max_total: int
    max_per_tool: int
    _total: int = field(default=0, init=False)
    _per_tool: dict[str, int] = field(default_factory=dict, init=False)

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(BeforeInvocationEvent, self._reset)
        registry.add_callback(BeforeToolCallEvent, self._check)

    def _reset(self, event: BeforeInvocationEvent) -> None:
        self._total = 0
        self._per_tool = {}

    def _check(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use.get("name", "<unknown>")
        total = self._total + 1
        per_tool = self._per_tool.get(name, 0) + 1

        if total > self.max_total:
            event.cancel_tool = (
                f"ツール呼び出し回数の上限 ({self.max_total} 回) に達しました。"
                "追加の調査はできません。ここまでに得た情報だけで結論をまとめてください。"
            )
            log_event(
                logger,
                logging.WARNING,
                "tool_call_limit_exceeded",
                scope="total",
                tool=name,
                limit=self.max_total,
            )
            return

        if per_tool > self.max_per_tool:
            event.cancel_tool = (
                f"ツール '{name}' の呼び出し回数の上限 ({self.max_per_tool} 回) に達しました。"
                "このツールはこれ以上使えません。別の手段か、手持ちの情報で進めてください。"
            )
            log_event(
                logger,
                logging.WARNING,
                "tool_call_limit_exceeded",
                scope="per_tool",
                tool=name,
                limit=self.max_per_tool,
            )
            return

        self._total = total
        self._per_tool[name] = per_tool

    @property
    def total_calls(self) -> int:
        return self._total


@dataclass
class TurnLimiter(HookProvider):
    """モデル呼び出し回数（ターン数）の上限。

    Strands には max_turns 相当の組み込み設定が無いため（1.52.0 時点）、
    BeforeModelCallEvent で自前に数える。
    """

    max_turns: int
    _turns: int = field(default=0, init=False)

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(BeforeInvocationEvent, self._reset)
        registry.add_callback(BeforeModelCallEvent, self._check)

    def _reset(self, event: BeforeInvocationEvent) -> None:
        self._turns = 0

    def _check(self, event: BeforeModelCallEvent) -> None:
        self._turns += 1
        if self._turns > self.max_turns:
            event.cancel = f"ターン数の上限 ({self.max_turns}) に達したため中断しました。"
            log_event(
                logger,
                logging.WARNING,
                "turn_limit_exceeded",
                limit=self.max_turns,
                turns=self._turns,
            )

    @property
    def turns(self) -> int:
        return self._turns


@dataclass
class UsageLogger(HookProvider):
    """1 リクエストあたりのトークン消費をログに出す。

    Strands の AgentResult.metrics.accumulated_usage を読む。
    role を持たせて、どのエージェントがいくら使ったかを分離して記録する。
    """

    role: str
    _last_usage: dict[str, int] = field(default_factory=dict, init=False)

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(AfterInvocationEvent, self._log)

    def _log(self, event: AfterInvocationEvent) -> None:
        metrics = getattr(getattr(event, "result", None), "metrics", None)
        if metrics is None:
            return
        usage = dict(getattr(metrics, "accumulated_usage", {}) or {})
        self._last_usage = {k: int(v) for k, v in usage.items() if isinstance(v, int)}
        log_event(
            logger,
            logging.INFO,
            "token_usage",
            role=self.role,
            input_tokens=usage.get("inputTokens"),
            output_tokens=usage.get("outputTokens"),
            total_tokens=usage.get("totalTokens"),
            cycle_count=getattr(metrics, "cycle_count", None),
        )

    @property
    def last_usage(self) -> dict[str, int]:
        return dict(self._last_usage)


@dataclass
class Guards:
    """1 エージェント分のガード一式。Agent(hooks=guards.hooks) で渡す。"""

    tool_limiter: ToolCallLimiter
    turn_limiter: TurnLimiter
    usage_logger: UsageLogger

    @property
    def hooks(self) -> list[HookProvider | HookCallback[Any]]:
        # 戻り値の型は Agent(hooks=...) が受け取る型に合わせている。
        # list は不変なので list[HookProvider] のままだと代入できない。
        return [self.tool_limiter, self.turn_limiter, self.usage_logger]


def build_guards(settings: Settings, role: str) -> Guards:
    return Guards(
        tool_limiter=ToolCallLimiter(
            max_total=settings.max_tool_calls_total,
            max_per_tool=settings.max_tool_calls_per_tool,
        ),
        turn_limiter=TurnLimiter(max_turns=settings.max_agent_turns),
        usage_logger=UsageLogger(role=role),
    )
