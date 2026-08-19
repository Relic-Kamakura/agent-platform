"""合格判定の共通設定。07-full-app のコードを import できるようにする。

AGENT_APP_DIR 環境変数で対象アプリを差し替えられる（模範解答の検証用）。
"""

from __future__ import annotations

import os
import pathlib
import sys

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = CHAPTER_DIR.parent
APP_DIR = pathlib.Path(os.environ.get("AGENT_APP_DIR", REPO_ROOT / "07-full-app"))

sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(CHAPTER_DIR))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _dummy_aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
