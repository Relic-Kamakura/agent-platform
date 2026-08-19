"""ツール層の検証。異常系がエージェントに読める形で返ることを固定する。"""

from __future__ import annotations

import httpx
import pytest

from src.config import Settings
from src.errors import (
    SearchProviderError,
    SearchProviderNotConfigured,
    SearchProviderRateLimited,
    SearchProviderTimeout,
)
from src.tools.providers import build_search_provider
from src.tools.providers.base import SearchResult
from src.tools.providers.mock import MockSearchProvider
from src.tools.providers.tavily import TavilySearchProvider
from src.tools.web_search import build_web_search_tool


def _call(tool, **kwargs) -> str:
    """@tool でラップされた関数を素の関数として呼ぶ。"""
    return tool.__wrapped__(**kwargs) if hasattr(tool, "__wrapped__") else tool(**kwargs)


class _FailingProvider:
    name = "failing"

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def search(self, query: str, max_results: int):
        raise self._exc


def test_mock_provider_is_deterministic() -> None:
    provider = MockSearchProvider()
    first = provider.search("pricing of acme", 5)
    second = provider.search("pricing of acme", 5)
    assert first == second
    assert all(r.url for r in first)


def test_mock_provider_falls_back_without_match() -> None:
    results = MockSearchProvider().search("まったく無関係な語", 5)
    assert len(results) == 1
    assert "mock" in results[0].snippet


def test_tool_returns_results_with_sources() -> None:
    tool = build_web_search_tool(MockSearchProvider(), Settings())
    out = _call(tool, query="acme pricing", max_results=5)
    assert "出典:" in out
    assert "https://" in out


def test_tool_clamps_max_results() -> None:
    tool = build_web_search_tool(MockSearchProvider(), Settings())
    assert "1 件" in _call(tool, query="feature", max_results=1)
    # 上限を超える指定でも例外にせず 20 に丸める
    assert "ERROR" not in _call(tool, query="feature", max_results=999)


@pytest.mark.parametrize(
    ("exc", "expect_retryable"),
    [
        (SearchProviderTimeout("timed out"), "yes"),
        (SearchProviderRateLimited("rate limited"), "no"),
        (SearchProviderError("boom"), "no"),
    ],
)
def test_tool_formats_errors_for_the_agent(exc: Exception, expect_retryable: str) -> None:
    tool = build_web_search_tool(_FailingProvider(exc), Settings())
    out = _call(tool, query="pricing")
    assert out.startswith("ERROR[")
    assert f"retryable: {expect_retryable}" in out
    assert "next_action:" in out


def test_tavily_requires_api_key() -> None:
    with pytest.raises(SearchProviderNotConfigured):
        TavilySearchProvider(api_key=None, timeout_seconds=1.0, max_retries=0)


def test_tavily_retries_then_raises_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"n": 0}

    class _Client:
        def __init__(self, *a, **k) -> None: ...
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, *a, **k):
            attempts["n"] += 1
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "Client", _Client)
    monkeypatch.setattr("src.tools.providers.tavily.time.sleep", lambda _s: None)

    provider = TavilySearchProvider(api_key="k", timeout_seconds=1.0, max_retries=2)
    with pytest.raises(SearchProviderTimeout):
        provider.search("q", 3)
    assert attempts["n"] == 3  # 初回 + リトライ 2 回


def test_tavily_parses_results(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Response:
        status_code = 200

        @staticmethod
        def json():
            return {"results": [{"title": "T", "url": "https://e.com", "content": "C"}]}

    class _Client:
        def __init__(self, *a, **k) -> None: ...
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, *a, **k):
            return _Response()

    monkeypatch.setattr(httpx, "Client", _Client)
    provider = TavilySearchProvider(api_key="k", timeout_seconds=1.0, max_retries=0)
    assert provider.search("q", 5) == [SearchResult(title="T", url="https://e.com", snippet="C")]


def test_build_search_provider_respects_setting() -> None:
    assert build_search_provider(Settings(search_provider="mock")).name == "mock"
    assert (
        build_search_provider(Settings(search_provider="tavily", tavily_api_key="k")).name
        == "tavily"
    )
