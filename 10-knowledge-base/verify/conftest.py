"""合格判定の共通設定。章ディレクトリ直下の学習者スクリプトを import できるようにする。"""

from __future__ import annotations

import pathlib
import sys

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAPTER_DIR))
