"""合格判定の共通設定。章内のパスを解決する。"""

from __future__ import annotations

import pathlib

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
TEST_FILE = CHAPTER_DIR / "exercises" / "test_fetch_page.py"
