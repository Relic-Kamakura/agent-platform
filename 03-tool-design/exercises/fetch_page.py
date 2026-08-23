"""ハンズオン 3.3: fetch_page ツール。

TODO を実装し、`uv run 01_call_fetch_page.py` で動かす。
実装が終わったら TODO コメントは消す。完成形は solutions/fetch_page.py。
"""

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
        """TODO(1): docstring を書く。モデルに渡る仕様書であり、このツールの実装の一部。

        3.2.1 の 3 節構成（受け取るもの / 返すもの / 含まないもの）で書く。
        「含まないもの」には、JavaScript 実行（動的レンダリング）をしないこと・
        認証が必要なページは取得できないことを必ず明記する。
        """
        # TODO(2): url が http:// / https:// で始まらなければ、取得を試みずに
        #   format_tool_error(PageFetchError("...")) を返す

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            # TODO(3): httpx.Client(timeout=timeout_seconds, follow_redirects=True) で GET する。
            #   - 200 系: response.text を max_chars で切り詰めて返す
            #   - 4xx: リトライしても直らないので、即 format_tool_error(...) を返す
            #   - 5xx と httpx.TimeoutException: last_error に控えて次の試行へ
            ...

            if attempt < max_retries:
                time.sleep(2**attempt)  # 指数バックオフ: 1s -> 2s -> 4s

        # TODO(4): 全試行が失敗したらエラーを ERROR[ 形式で返す。
        #   タイムアウトなら PageFetchTimeout、それ以外は PageFetchError を使う
        ...

    return fetch_page
