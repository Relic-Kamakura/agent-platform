"""検索プロバイダの生成。"""

from __future__ import annotations

from ...config import Settings
from .base import SearchProvider, SearchResult
from .mock import MockSearchProvider
from .tavily import TavilySearchProvider

__all__ = [
    "SearchProvider",
    "SearchResult",
    "MockSearchProvider",
    "TavilySearchProvider",
    "build_search_provider",
]


def build_search_provider(settings: Settings) -> SearchProvider:
    if settings.search_provider == "tavily":
        return TavilySearchProvider(
            api_key=settings.tavily_api_key,
            timeout_seconds=settings.http_timeout_seconds,
            max_retries=settings.http_max_retries,
        )
    return MockSearchProvider()
