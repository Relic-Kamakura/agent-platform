"""合格判定の共通設定。exercises/ の学習者コードを import できるようにする。"""

from __future__ import annotations

import pathlib
import sys

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAPTER_DIR / "exercises"))

import pytest  # noqa: E402


@pytest.fixture()
def fetch_page_module():
    import fetch_page

    return fetch_page


@pytest.fixture()
def fetch_page_tool(fetch_page_module):
    tool = fetch_page_module.build_fetch_page_tool(timeout_seconds=1.0, max_retries=2)
    # @tool でラップされていても素の関数を取り出して呼ぶ
    return getattr(tool, "__wrapped__", tool)
