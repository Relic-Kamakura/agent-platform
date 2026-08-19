"""テスト共通設定。

BedrockModel はコンストラクタ内で boto3 クライアントを生成するため、
構築するだけでも認証情報の解決が走る（ネットワークアクセスは発生しない）。
テストを AWS 環境から独立させるため、ダミーの認証情報を注入する。
実際のモデル呼び出しはテストしない。
"""

from __future__ import annotations

import pytest

from src.config import get_settings


@pytest.fixture(autouse=True)
def _isolate_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # 開発者の .env / 実 AWS プロファイルの影響を受けないようにする
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    get_settings.cache_clear()
