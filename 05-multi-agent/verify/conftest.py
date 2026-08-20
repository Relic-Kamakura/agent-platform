from __future__ import annotations

import os
import pathlib
import sys

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = CHAPTER_DIR.parent
APP_DIR = pathlib.Path(os.environ.get("AGENT_APP_DIR", REPO_ROOT / "07-full-app"))

sys.path.insert(0, str(APP_DIR))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _dummy_aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    # エージェント構築時に boto3 クライアントが作られるため（troubleshooting.md 参照）
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)


@pytest.fixture()
def pricing_module():
    try:
        from src.agents import pricing_agent  # type: ignore[attr-defined]
    except ImportError:
        pytest.fail(
            "07-full-app/src/agents/pricing_agent.py がまだありません。"
            "README の 5.3 ハンズオンの要件に沿って実装してください。"
        )
    return pricing_agent
