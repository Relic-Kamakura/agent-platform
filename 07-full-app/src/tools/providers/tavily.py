"""Tavily Search API プロバイダ。

外部 API 呼び出しなので、タイムアウトと指数バックオフによるリトライを持つ。
失敗は例外として送出する。呼び出し側（ツール層）がエージェント向けに整形する。
"""

from __future__ import annotations

import logging
import time

import httpx

from ...errors import (
    SearchProviderError,
    SearchProviderNotConfigured,
    SearchProviderRateLimited,
    SearchProviderTimeout,
)
from ...observability import log_event
from .base import SearchResult

logger = logging.getLogger(__name__)

_ENDPOINT = "https://api.tavily.com/search"


class TavilySearchProvider:
    """Tavily の /search を叩く。"""

    name = "tavily"

    def __init__(self, api_key: str | None, timeout_seconds: float, max_retries: int) -> None:
        if not api_key:
            raise SearchProviderNotConfigured("TAVILY_API_KEY が設定されていません。")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_retries = max_retries

    def search(self, query: str, max_results: int) -> list[SearchResult]:
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }
        last_error: Exception | None = None

        # 試行回数 = 初回 + リトライ回数。リトライ対象は timeout / 429 / 5xx のみ。
        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(_ENDPOINT, json=payload)
            except httpx.TimeoutException as exc:
                last_error = exc
                log_event(
                    logger,
                    logging.WARNING,
                    "search_timeout",
                    provider=self.name,
                    attempt=attempt + 1,
                )
            else:
                if response.status_code == 429:
                    raise SearchProviderRateLimited("Tavily にレート制限されました。")
                if response.status_code >= 500:
                    last_error = SearchProviderError(
                        f"Tavily が {response.status_code} を返しました。"
                    )
                    log_event(
                        logger,
                        logging.WARNING,
                        "search_server_error",
                        provider=self.name,
                        status=response.status_code,
                        attempt=attempt + 1,
                    )
                elif response.status_code >= 400:
                    # クライアント側の誤りはリトライしても直らない。即座に失敗させる。
                    raise SearchProviderError(
                        f"Tavily が {response.status_code} を返しました: {response.text[:200]}"
                    )
                else:
                    return self._parse(response.json(), max_results)

            if attempt < self._max_retries:
                time.sleep(2**attempt)

        if isinstance(last_error, httpx.TimeoutException):
            raise SearchProviderTimeout(
                f"Tavily が {self._max_retries + 1} 回のいずれもタイムアウトしました "
                f"(timeout={self._timeout}s)。"
            ) from last_error
        raise SearchProviderError(f"Tavily の呼び出しに失敗しました: {last_error}") from last_error

    @staticmethod
    def _parse(body: dict, max_results: int) -> list[SearchResult]:
        results = body.get("results")
        if not isinstance(results, list):
            raise SearchProviderError("Tavily のレスポンスに results 配列が含まれていません。")
        parsed = [
            SearchResult(
                title=str(item.get("title", "")).strip() or "(タイトルなし)",
                url=str(item.get("url", "")).strip(),
                snippet=str(item.get("content", "")).strip(),
            )
            for item in results
            if isinstance(item, dict) and item.get("url")
        ]
        return parsed[:max_results]
