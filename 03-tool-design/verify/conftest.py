from __future__ import annotations

import os
import pathlib
import sys

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = CHAPTER_DIR.parent
APP_DIR = pathlib.Path(os.environ.get("AGENT_APP_DIR", REPO_ROOT / "07-full-app"))

sys.path.insert(0, str(APP_DIR))

import pytest  # noqa: E402


@pytest.fixture()
def fetch_page_module():
    try:
        from src.tools import fetch_page  # type: ignore[attr-defined]
    except ImportError:
        pytest.fail(
            "07-full-app/src/tools/fetch_page.py がまだありません。"
            "README の 3.5 ハンズオンの要件に沿って実装してください。"
        )
    return fetch_page


@pytest.fixture()
def fetch_page_tool(fetch_page_module):
    from src.config import Settings

    tool = fetch_page_module.build_fetch_page_tool(
        Settings(http_timeout_seconds=1.0, http_max_retries=2)
    )
    # @tool でラップされていても素の関数を取り出して呼ぶ
    return getattr(tool, "__wrapped__", tool)
