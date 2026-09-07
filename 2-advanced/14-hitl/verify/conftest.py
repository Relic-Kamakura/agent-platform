"""合格判定の共通設定。exercises/ の学習者コードを import できるようにする。"""

from __future__ import annotations

import pathlib
import sys

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAPTER_DIR / "exercises"))

import pytest  # noqa: E402


@pytest.fixture()
def approval_gate_cls():
    from approval_gate import ApprovalGate

    return ApprovalGate
