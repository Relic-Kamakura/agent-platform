"""Web 検索ツール。

1 ツール 1 責務: 「クエリを受け取り、検索結果の一覧を返す」のみを行う。
要約も、結果の取捨選択も、フォローアップ検索もしない。それらはエージェントの仕事。
"""

from __future__ import annotations

import logging

from strands import tool

from ..config import Settings
from ..errors import ToolError, format_tool_error
from ..observability import log_event
from .providers import SearchProvider

logger = logging.getLogger(__name__)


def build_web_search_tool(provider: SearchProvider, settings: Settings):
    """設定済みのプロバイダを束縛した web_search ツールを返す。

    ツール関数から Settings やプロバイダをグローバル参照させないための工夫。
    """

    default_max_results = settings.search_max_results

    @tool
    def web_search(query: str, max_results: int = default_max_results) -> str:
        """Web を検索し、一致したページの一覧を返す。

        競合他社の価格、機能、公開情報など、モデルの知識に無い、または古くなっている
        可能性がある事実を確認したいときに使う。

        受け取るもの:
            query: 検索クエリ。自然文でも単語の並びでもよい。1 つの調査観点につき
                1 回の呼び出しにすること。複数の観点を 1 つのクエリに詰め込まない。
            max_results: 返す最大件数。1 以上 20 以下。既定は設定値。

        返すもの:
            見つかったページごとに「タイトル」「要約スニペット」「出典 URL」を並べた
            Markdown 形式の文字列。ヒットが 0 件の場合はその旨の文字列を返す。
            失敗した場合は "ERROR[...]" で始まる文字列を返し、retryable と
            next_action を含める。

        含まないもの:
            - ページ本文の全文。スニペットのみで、本文取得は行わない。
            - 結果の要約・評価・順位付け。生の検索結果をそのまま返す。
            - 認証が必要なページ、ログインの背後にある情報。
            - 検索結果の正確性の保証。内容は必ず出典 URL とともに扱うこと。
        """
        bounded = max(1, min(int(max_results), 20))
        try:
            results = provider.search(query, bounded)
        except ToolError as exc:
            # 握りつぶさず、エージェントが次の判断をできる形に整形して返す。
            log_event(
                logger,
                logging.WARNING,
                "web_search_failed",
                provider=provider.name,
                query=query,
                error=type(exc).__name__,
            )
            return format_tool_error(exc)

        log_event(
            logger,
            logging.INFO,
            "web_search",
            provider=provider.name,
            query=query,
            hits=len(results),
        )

        if not results:
            return f"クエリ '{query}' に一致する結果は 0 件でした。"

        header = f"クエリ '{query}' の検索結果 {len(results)} 件:"
        return header + "\n" + "\n".join(r.to_markdown() for r in results)

    return web_search
