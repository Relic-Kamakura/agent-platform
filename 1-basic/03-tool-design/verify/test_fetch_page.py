"""演習 03 の合格判定。要求仕様のテスト表現でもある。"""

from __future__ import annotations

import pathlib

import httpx
import pytest


def test_no_todo_left(fetch_page_module) -> None:
    source = pathlib.Path(fetch_page_module.__file__).read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/fetch_page.py に TODO が残っています。README 3.3 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


# --- docstring: LLM 向け仕様書になっているか --------------------------------
def test_docstring_has_required_sections(fetch_page_module) -> None:
    tool = fetch_page_module.build_fetch_page_tool(timeout_seconds=1.0, max_retries=2)
    fn = getattr(tool, "__wrapped__", tool)
    doc = fn.__doc__ or ""
    for section in ("受け取るもの", "返すもの", "含まないもの"):
        assert section in doc, f"docstring に「{section}」の節がありません。"
    assert "JavaScript" in doc or "動的" in doc, (
        "「含まないもの」に JavaScript 実行（動的レンダリング）をしないことを明記してください。"
    )
    assert "認証" in doc, "「含まないもの」に認証が必要なページを扱えないことを明記してください。"


# --- 正常系 -------------------------------------------------------------------
class _Response:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code


def _client_returning(response_factory):
    class _Client:
        def __init__(self, *args, **kwargs) -> None:
            # タイムアウトがハードコードでなく注入値から来ていることを検査する
            _client_returning.captured_timeout = kwargs.get("timeout")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, *args, **kwargs):
            return response_factory()

    return _Client


def test_returns_body_truncated(monkeypatch: pytest.MonkeyPatch, fetch_page_tool) -> None:
    monkeypatch.setattr(httpx, "Client", _client_returning(lambda: _Response("abc" * 10_000)))
    out = fetch_page_tool(url="https://example.com", max_chars=100)
    assert not out.startswith("ERROR[")
    assert len(out) <= 200, "本文が max_chars 付近で切り詰められていません（コンテキスト爆発防止）。"


def test_timeout_comes_from_settings(monkeypatch: pytest.MonkeyPatch, fetch_page_tool) -> None:
    monkeypatch.setattr(httpx, "Client", _client_returning(lambda: _Response("ok")))
    fetch_page_tool(url="https://example.com")
    assert _client_returning.captured_timeout == 1.0, (
        "httpx.Client の timeout に build_fetch_page_tool の timeout_seconds が渡っていません。"
    )


# --- 異常系: エージェントが読める形で返るか -----------------------------------
def test_rejects_non_http_url(fetch_page_tool) -> None:
    out = fetch_page_tool(url="file:///etc/passwd")
    assert out.startswith("ERROR["), "http/https 以外は取得を試みず ERROR[ 形式で拒否してください。"
    assert "retryable" in out and "next_action" in out


def test_timeout_is_retried_then_reported(
    monkeypatch: pytest.MonkeyPatch, fetch_page_tool
) -> None:
    calls = {"n": 0}

    def _raise():
        calls["n"] += 1
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "Client", _client_returning(_raise))
    monkeypatch.setattr("time.sleep", lambda _s: None)

    out = fetch_page_tool(url="https://example.com")
    assert out.startswith("ERROR["), "リトライ後も失敗したら ERROR[ 形式で返してください。"
    assert calls["n"] == 3, f"初回 + リトライ 2 回 = 3 回の試行が必要です（実際: {calls['n']} 回）。"
    assert "retryable" in out


def test_4xx_is_not_retried(monkeypatch: pytest.MonkeyPatch, fetch_page_tool) -> None:
    calls = {"n": 0}

    def _forbidden():
        calls["n"] += 1
        return _Response("forbidden", status_code=403)

    monkeypatch.setattr(httpx, "Client", _client_returning(_forbidden))
    out = fetch_page_tool(url="https://example.com/secret")
    assert out.startswith("ERROR[")
    assert calls["n"] == 1, "4xx はリトライしても直りません。1 回で諦めてください。"
