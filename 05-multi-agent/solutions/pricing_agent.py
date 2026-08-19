"""演習 05 の模範解答。07-full-app/src/agents/pricing_agent.py として配置する。

PricingAgent: 価格情報の調査と比較表への整形だけを担当する。

モデル割り当ての理由:
    価格を検索して表に整形するのは定型処理で、判断らしい判断が無い。
    軽量モデル (search ロール = MODEL_ID_SEARCH) で足りる。
    どの競合を比較すべきかの判断は呼び出し側 (Orchestrator) の仕事。
"""

from __future__ import annotations

import logging

from strands import Agent, tool

from ..config import Settings
from ..guards import build_guards
from ..observability import log_event
from ..tools.providers import build_search_provider
from ..tools.web_search import build_web_search_tool
from .models import build_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
あなたは競合リサーチの価格調査担当です。指定された企業・製品の価格情報だけを
Web で調べ、Markdown の比較表にまとめます。

守ること:
- web_search で裏を取っていない価格を書かない。
- 確認できないセルは「不明」とする。推測で埋めない。
- 表の下に、使用した出典 URL を列挙する。
- 価格以外の情報（機能、評判）は調べない。表に含めない。
"""


def build_pricing_agent_tool(settings: Settings):
    """PricingAgent を Orchestrator 向けのツールとして公開する。"""

    provider = build_search_provider(settings)
    guards = build_guards(settings, role="pricing")
    agent = Agent(
        name="PricingAgent",
        # 表への整形は定型処理なので軽量モデル（search ロール）で足りる
        model=build_model(settings, "search"),
        system_prompt=SYSTEM_PROMPT,
        tools=[build_web_search_tool(provider, settings)],
        hooks=guards.hooks,
        callback_handler=None,
    )

    @tool
    def compare_pricing(companies: str) -> str:
        """指定された企業・製品の価格を調べ、Markdown の比較表で返す。

        利用者が価格の比較を求めているときに使う。

        受け取るもの:
            companies: 比較したい企業・製品名を読点やカンマで並べた文字列。
                例: 「Acme Analytics, Globex Insights」。2 つ以上を渡すこと。

        返すもの:
            行 = 企業、列 = プラン/価格の Markdown 表。確認できなかったセルは「不明」。
            表の下に出典 URL の一覧が付く。

        含まないもの:
            - 価格以外の情報（機能・評判・シェア）。それらは investigate を使うこと。
            - どちらが安い/優れているかの判断。判断はあなた（呼び出し側）の仕事。
        """
        result = agent(f"次の企業の価格を比較してください: {companies}")
        log_event(
            logger,
            logging.INFO,
            "pricing_agent_invoked",
            companies=companies,
            cycles=getattr(result.metrics, "cycle_count", None),
        )
        return str(result.message)

    return compare_pricing
