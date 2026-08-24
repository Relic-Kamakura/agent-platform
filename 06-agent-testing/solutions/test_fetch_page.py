"""ハンズオン 6.3 の模範解答。exercises/test_fetch_page.py の完成形。

各テストに「このテストが落ちるのはどんなバグが入ったときか」を書いている。
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "target"))

import httpx
import pytest

from fetch_page import build_fetch_page_tool


def _tool():
    """テスト対象。タイムアウト 1 秒・リトライ 2 回で束縛し、@tool のラップを外す。"""
    tool = build_fetch_page_tool(timeout_seconds=1.0, max_retries=2)
    return getattr(tool, "__wrapped__", tool)


class _Response:
    """httpx のレスポンスの偽物。テストが使う属性だけを持つ。"""

    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code


def _client(response_factory):
    """httpx.Client と差し替える偽クラスを作る。get() が response_factory の結果を返す。"""

    class _Client:
        def __init__(self, *args, **kwargs) -> None: ...

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, *args, **kwargs):
            return response_factory()

    return _Client


def test_returns_truncated_body(monkeypatch: pytest.MonkeyPatch) -> None:
    # 落ちるとき: 切り詰めを忘れて巨大ページがコンテキストに流れ込むバグ
    monkeypatch.setattr(httpx, "Client", _client(lambda: _Response("x" * 100_000)))
    out = _tool()(url="https://example.com", max_chars=500)
    assert not out.startswith("ERROR[")
    assert len(out) <= 600


def test_non_http_url_is_rejected_without_network() -> None:
    # 落ちるとき: file:// などを取得しようとする（SSRF の芽）
    out = _tool()(url="ftp://example.com/data")
    assert out.startswith("ERROR[")
    assert "next_action" in out


def test_timeout_retries_then_reports(monkeypatch: pytest.MonkeyPatch) -> None:
    # 落ちるとき: リトライ回数が設定と乖離する、または例外を握りつぶすバグ
    calls = {"n": 0}

    def _raise():
        calls["n"] += 1
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "Client", _client(_raise))
    monkeypatch.setattr("time.sleep", lambda _s: None)

    out = _tool()(url="https://example.com")
    assert out.startswith("ERROR[")
    assert calls["n"] == 3  # 初回 + リトライ 2 回
    assert "retryable" in out


def test_404_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    # 落ちるとき: 4xx をリトライして無駄に待つバグ
    calls = {"n": 0}

    def _not_found():
        calls["n"] += 1
        return _Response("not found", status_code=404)

    monkeypatch.setattr(httpx, "Client", _client(_not_found))
    out = _tool()(url="https://example.com/gone")
    assert out.startswith("ERROR[")
    assert calls["n"] == 1


def test_server_error_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    # 落ちるとき: 一時的な 5xx で即諦めて成功率が下がるバグ
    calls = {"n": 0}

    def _flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            return _Response("oops", status_code=503)
        return _Response("recovered")

    monkeypatch.setattr(httpx, "Client", _client(_flaky))
    monkeypatch.setattr("time.sleep", lambda _s: None)

    out = _tool()(url="https://example.com")
    assert out == "recovered"
    assert calls["n"] == 3
