"""テスト対象の fetch_page（編集不要）。第3章のハンズオンで作ったものと同じ完成品。"""

from __future__ import annotations

import time

import httpx
from strands import tool


class PageFetchError(Exception):
    """ページ取得の失敗。retryable と hint がモデルへの返答に含まれる。"""

    retryable = False
    hint = "この URL の本文は取得できません。検索結果のスニペットの範囲で報告してください。"


class PageFetchTimeout(PageFetchError):
    """タイムアウト。時間を置けば直る可能性があるので retryable。"""

    retryable = True
    hint = "時間を置いて再試行するか、別の出典を使ってください。"


def format_tool_error(exc: PageFetchError) -> str:
    """例外を、モデルが読んで次の判断ができる文字列に整形する。"""
    return "\n".join(
        [
            f"ERROR[{type(exc).__name__}]: {exc}",
            f"retryable: {'yes' if exc.retryable else 'no'}",
            f"next_action: {exc.hint}",
        ]
    )


def build_fetch_page_tool(timeout_seconds: float, max_retries: int):
    """タイムアウトとリトライ回数を束縛した fetch_page ツールを返す。

    値をコードに書かず外から注入するための作り。
    """

    @tool
    def fetch_page(url: str, max_chars: int = 4000) -> str:
        """指定した URL のページ本文テキストを取得して返す。

        検索結果のスニペットだけでは情報が足りず、出典ページの本文を確認したいときに使う。

        受け取るもの:
            url: 取得したいページの URL。http:// か https:// で始まるものだけを渡すこと。
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
                with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
                    response = client.get(url)
            except httpx.TimeoutException as exc:
                last_error = exc
            else:
                if response.status_code >= 500:
                    last_error = PageFetchError(f"{url} が {response.status_code} を返しました。")
                elif response.status_code >= 400:
                    # 4xx はリトライしても直らない。即座に報告する
                    return format_tool_error(
                        PageFetchError(f"{url} が {response.status_code} を返しました。")
                    )
                else:
                    return response.text[:max_chars]

            if attempt < max_retries:
                time.sleep(2**attempt)

        if isinstance(last_error, httpx.TimeoutException):
            return format_tool_error(
                PageFetchTimeout(
                    f"{url} の取得が {max_retries + 1} 回ともタイムアウトしました。"
                )
            )
        return format_tool_error(PageFetchError(f"{url} の取得に失敗しました: {last_error}"))

    return fetch_page
