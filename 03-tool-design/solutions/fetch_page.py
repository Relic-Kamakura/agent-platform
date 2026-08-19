"""演習 03 の模範解答。07-full-app/src/tools/fetch_page.py として配置する。

Web ページ本文の取得ツール。
1 ツール 1 責務: 「URL を受け取り、本文テキストを返す」のみ。要約・抽出はしない。
"""

from __future__ import annotations

import logging
import time

import httpx
from strands import tool

from ..config import Settings
from ..errors import SearchProviderTimeout, ToolError, format_tool_error
from ..observability import log_event

logger = logging.getLogger(__name__)


class PageFetchError(ToolError):
    """ページ取得の失敗。"""

    retryable = False
    hint = "この URL の本文は取得できません。検索結果のスニペットの範囲で報告してください。"


def build_fetch_page_tool(settings: Settings):
    """設定を束縛した fetch_page ツールを返す。"""

    timeout = settings.http_timeout_seconds
    max_retries = settings.http_max_retries

    @tool
    def fetch_page(url: str, max_chars: int = 4000) -> str:
        """指定した URL のページ本文テキストを取得して返す。

        検索結果のスニペットだけでは情報が足りず、出典ページの本文を確認したいときに使う。

        受け取るもの:
            url: 取得したいページの URL。http:// か https:// で始まるものだけを渡すこと。
                web_search の結果に含まれる出典 URL をそのまま渡すのが典型的な使い方。
            max_chars: 返す本文の最大文字数。既定 4000。長いページは先頭から切り詰められる。

        返すもの:
            ページ本文のテキスト（max_chars で切り詰め済み）。
            失敗した場合は "ERROR[...]" で始まる文字列を返し、retryable と next_action を含む。

        含まないもの:
            - JavaScript の実行。動的レンダリングが必要なページは本文が取れないことがある。
            - 認証が必要なページ、ログインの背後にある情報。
            - HTML の整形・要約・抽出。生のテキストをそのまま返す。要約はあなたの仕事。
        """
        if not url.startswith(("http://", "https://")):
            return format_tool_error(
                PageFetchError(f"http/https 以外の URL は取得できません: {url}")
            )

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    response = client.get(url)
            except httpx.TimeoutException as exc:
                last_error = exc
            else:
                if response.status_code >= 500:
                    last_error = PageFetchError(f"{url} が {response.status_code} を返しました。")
                elif response.status_code >= 400:
                    # 4xx はリトライしても直らない。即座に報告する。
                    return format_tool_error(
                        PageFetchError(f"{url} が {response.status_code} を返しました。")
                    )
                else:
                    body = response.text[:max_chars]
                    log_event(logger, logging.INFO, "fetch_page", url=url, chars=len(body))
                    return body

            if attempt < max_retries:
                time.sleep(2**attempt)

        if isinstance(last_error, httpx.TimeoutException):
            return format_tool_error(
                SearchProviderTimeout(
                    f"{url} の取得が {max_retries + 1} 回ともタイムアウトしました。"
                )
            )
        return format_tool_error(PageFetchError(f"{url} の取得に失敗しました: {last_error}"))

    return fetch_page
