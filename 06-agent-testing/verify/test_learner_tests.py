"""演習 06 の合格判定。受講者が書いたテストそのものを検査・実行する。"""

from __future__ import annotations

import ast
import subprocess
import sys

import pytest

from conftest import APP_DIR

TEST_FILE = APP_DIR / "tests" / "test_fetch_page.py"


def _source() -> str:
    if not TEST_FILE.exists():
        pytest.fail(
            "07-full-app/tests/test_fetch_page.py がまだありません。README の 6.3 ハンズオンを確認してください。"
        )
    return TEST_FILE.read_text(encoding="utf-8")


def test_has_at_least_four_test_functions() -> None:
    tree = ast.parse(_source())
    test_functions = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    ]
    assert len(test_functions) >= 4, (
        f"テスト関数が {len(test_functions)} 個です。4 個以上書いてください: {test_functions}"
    )


def test_mocks_httpx_instead_of_real_network() -> None:
    source = _source()
    assert "monkeypatch" in source or "mock" in source.lower(), (
        "httpx をモックしてください。実ネットワークに依存するテストは CI で使えません。"
    )
    assert "httpx" in source, "httpx のモック（_Client パターン等）が見つかりません。"


def test_covers_error_format() -> None:
    assert "ERROR[" in _source(), (
        "異常系テストがありません。失敗時に ERROR[ 形式で返ることを assert してください。"
    )


def test_learner_tests_actually_pass() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_fetch_page.py", "-q", "--no-header"],
        cwd=APP_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        "書いたテストが通っていません:\n" + result.stdout[-2000:] + result.stderr[-1000:]
    )
