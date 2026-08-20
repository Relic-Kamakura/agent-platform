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
def cost_limiter_cls():
    try:
        from src.guards import CostLimiter  # type: ignore[attr-defined]
    except ImportError:
        pytest.fail(
            "src/guards.py に CostLimiter がまだありません。README の 4.3 ハンズオンの要件を確認してください。"
        )
    return CostLimiter
