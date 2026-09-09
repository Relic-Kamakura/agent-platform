"""SearchAgent: Web 検索の実行と、結果の事実抽出のみを担当する。

モデル割り当ての理由:
    クエリの整形と、検索結果から事実を抜き出す定型処理しか行わない。
    判断らしい判断が無いので、軽量モデル (MODEL_ID_SEARCH) を割り当てている。

Orchestrator からは「ツール」として呼ばれる (agents-as-tools)。
どの観点を何回調べるかは Orchestrator の裁量に委ねたいため、決定的な呼び出しにしていない。

Agent はツール呼び出しごとに新しく作る。Strands の Agent は同じインスタンスの並行実行を
ConcurrencyException で拒否するため、Orchestrator が同一ターンで investigate を 2 回要求すると
共有インスタンスでは 2 回目が失敗する。会話履歴が呼び出し間で引き継がれるのも避けたい。
BedrockModel（boto3 クライアント）はスレッドセーフなので共有する。


"""

from __future__ import annotations

import logging

from strands import Agent, tool
from strands.models import BedrockModel

from ..config import Settings
from ..guards import build_guards
from ..observability import log_event
from ..tools.providers import build_search_provider
from ..tools.web_search import build_web_search_tool
from .models import build_model
from .results import result_text

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
あなたは競合リサーチの調査担当です。与えられた 1 つの調査観点について Web を検索し、
確認できた事実だけを報告します。

守ること:
- web_search ツールで裏を取っていない情報は書かない。推測を事実として書かない。
- 事実には必ず出典 URL を添える。
- 検索しても分からなかったことは「確認できず」と明記する。埋め合わせに推測を書かない。
- 意見、評価、優劣の判断は書かない。事実の列挙に徹する。
- 出力は箇条書きで簡潔に。
"""


def build_search_agent(settings: Settings, model: BedrockModel | None = None) -> Agent:
    provider = build_search_provider(settings)
    guards = build_guards(settings, role="search")
    return Agent(
        name="SearchAgent",
        model=model or build_model(settings, "search"),
        system_prompt=SYSTEM_PROMPT,
        tools=[build_web_search_tool(provider, settings)],
        hooks=guards.hooks,
        callback_handler=None,
    )


def build_search_agent_tool(settings: Settings, model: BedrockModel | None = None):
    """SearchAgent を Orchestrator 向けのツールとして公開する。"""

    shared_model = model or build_model(settings, "search")

    @tool
    def investigate(topic: str) -> str:
        """1 つの調査観点について Web を調べ、確認できた事実を返す。

        競合の価格、機能、市場動向など、外部情報の裏取りが必要なときに使う。

        受け取るもの:
            topic: 調べたい観点を 1 つだけ書いた文。
                例: 「Acme Analytics の料金プラン」。
                複数の観点をまとめて渡さない。観点ごとに 1 回ずつ呼び出すこと。

        返すもの:
            確認できた事実の箇条書き。各項目に出典 URL が付く。
            確認できなかった点は「確認できず」と明記された文字列。

        含まないもの:
            - 競合同士の比較や優劣の判断。統合はあなた（呼び出し側）の仕事。
            - 出典の無い推測。
            - 調査観点の分解。渡された観点をそのまま調べるだけ。
        """
        agent = build_search_agent(settings, model=shared_model)
        result = agent(topic)
        text = result_text(result)
        # 本文（観点の文言）はログに出さない。長さと周回数だけ記録する。
        log_event(
            logger,
            logging.INFO,
            "search_agent_invoked",
            topic_length=len(topic),
            cycles=getattr(result.metrics, "cycle_count", None),
        )
        return text

    return investigate
