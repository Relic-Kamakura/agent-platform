"""ハンズオン 6.3: fetch_page のテスト。

TODO のテストを追加し、`uv run pytest exercises/test_fetch_page.py -q` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/test_fetch_page.py。
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "target"))

import httpx
import pytest

from fetch_page import build_fetch_page_tool


def _tool():
    """テスト対象。タイムアウト 1 秒・リトライ 2 回で固定し、@tool のラップを外す。"""
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


# TODO(1): 異常系のテストを書く。httpx をモックして失敗（4xx など）を再現し、
#   返り値が "ERROR[" で始まることを assert する。
#   例外を起こしたいときは response_factory の中で raise すればよい。

# TODO(2): リトライ回数のテストを書く。タイムアウトを起こし続け、試行がちょうど
#   3 回（初回 + リトライ 2 回）で止まることを回数カウンタで assert する。
#   monkeypatch.setattr("time.sleep", lambda _s: None) で待ち時間を消すこと。

# TODO(3): 自分で観点をもう 1 つ決めてテストを書き、合計 4 本以上にする。
#   候補: 4xx がリトライされないこと、http/https 以外の URL が拒否されること、
#   5xx が途中で復旧したら本文が返ること。
