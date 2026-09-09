"""ハンズオン 6.3: fetch_page と verdict のテスト。

TODO のテストを追加し、`uv run pytest exercises/test_fetch_page.py -q` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/test_fetch_page.py。
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "target"))

import httpx
import pytest
from strands.agent.agent_result import AgentResult
from strands.telemetry.metrics import EventLoopMetrics

from fetch_page import build_fetch_page_tool
from verdict import parse_verdict


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


def _agent_result(text: str) -> AgentResult:
    """モデルを呼ばずに AgentResult を組む。Agent と後続処理の境界を試すための材料。"""
    return AgentResult(
        stop_reason="end_turn",
        message={"role": "assistant", "content": [{"text": text}]},
        metrics=EventLoopMetrics(),
        state={},
    )


def test_returns_truncated_body(monkeypatch: pytest.MonkeyPatch) -> None:
    # 落ちるとき: 切り詰めを忘れて巨大ページがコンテキストに流れ込むバグ
    monkeypatch.setattr(httpx, "Client", _client(lambda: _Response("x" * 100_000)))
    out = _tool()(url="https://example.com", max_chars=500)
    assert not out.startswith("ERROR[")
    assert len(out) <= 600


# TODO(1): URL 検証のテストを書く。"ftp://example.com" のような URL を渡し、httpx を
#   モックせずに（ネットワークを呼ばずに）返り値が "ERROR[" で始まることを assert する。

# TODO(2): 4xx のテストを書く。404 を返すモックで、返り値が "ERROR[" で始まり、
#   試行が 1 回で止まる（リトライしない）ことを回数カウンタで assert する。

# TODO(3): リトライ回数のテストを書く。タイムアウトを起こし続け、試行がちょうど
#   3 回（初回 + リトライ 2 回）で止まることを回数カウンタで assert する。
#   例外を起こしたいときは response_factory の中で raise すればよい。
#   monkeypatch.setattr("time.sleep", lambda _s: None) で待ち時間を消すこと。

# TODO(4): 5xx のテストを書く。503 を 2 回返したあと 200 を返すモックで、
#   リトライの末に本文が返ることを assert する。

# TODO(5): Agent の応答を受け取る境界のテストを書く。_agent_result("VERDICT: ok\n指摘なし")
#   で AgentResult を手で組み、parse_verdict がその本文から "ok" を読めることを assert する。
#   あわせて str(result.message) が dict の文字列表現であること（本文ではないこと）も assert する。

# TODO(6): target/fetch_page.py を読み、上記でテストされていない分岐を 2 つ見つけて
#   テストを書く。合計 8 本以上にする。
