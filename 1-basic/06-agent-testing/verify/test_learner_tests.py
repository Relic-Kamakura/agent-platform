"""演習 06 の合格判定。学習者が書いたテストそのものを検査し、実行する。"""

from __future__ import annotations

import ast
import subprocess
import sys

import pytest

from conftest import CHAPTER_DIR, TEST_FILE


def _source() -> str:
    if not TEST_FILE.exists():
        pytest.fail(
            "exercises/test_fetch_page.py がありません。README の 6.3 ハンズオンを確認してください。"
        )
    return TEST_FILE.read_text(encoding="utf-8")


def test_no_todo_left() -> None:
    assert "TODO" not in _source(), (
        "exercises/test_fetch_page.py に TODO が残っています。README 6.3.1 に沿ってテストを追加し、"
        "終わったら TODO コメントを消してください。"
    )


def test_has_at_least_eight_test_functions() -> None:
    tree = ast.parse(_source())
    test_functions = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    ]
    assert len(test_functions) >= 8, (
        f"テスト関数が {len(test_functions)} 個です。README 6.3 の要件どおり 8 個以上書いてください: {test_functions}"
    )


def test_mocks_httpx_instead_of_real_network() -> None:
    source = _source()
    assert "monkeypatch" in source or "mock" in source.lower(), (
        "httpx をモックしてください。実ネットワークに依存するテストは CI で使えません。"
    )
    assert "httpx" in source, "httpx のモック（_client パターン等）が見つかりません。"


def test_covers_error_format() -> None:
    assert "ERROR[" in _source(), (
        "異常系テストがありません。失敗時に ERROR[ 形式で返ることを assert してください。"
    )


def test_covers_agent_result_boundary() -> None:
    tree = ast.parse(_source())
    called = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "parse_verdict"
        for node in ast.walk(tree)
    )
    assert called, (
        "Agent の応答を受け取る境界のテストがありません。AgentResult を手で組んで "
        "parse_verdict に渡すテストを書いてください（README 6.2.2）。"
    )


def test_learner_tests_actually_pass() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "exercises/test_fetch_page.py", "-q", "--no-header"],
        cwd=CHAPTER_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        "書いたテストが通っていません:\n" + result.stdout[-2000:] + result.stderr[-1000:]
    )
