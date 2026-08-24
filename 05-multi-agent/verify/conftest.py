"""合格判定の共通設定。exercises/ の学習者コードを import できるようにする。"""

from __future__ import annotations

import pathlib
import sys

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAPTER_DIR / "exercises"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _dummy_aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    # エージェント構築時に boto3 クライアントが作られるため（docs/troubleshooting.md 参照）
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)


@pytest.fixture()
def specialist_module():
    import specialist

    return specialist
