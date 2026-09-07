from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _dummy_aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    # BedrockModel はコンストラクタで boto3 クライアントを作るため（第6章参照）、
    # モジュール import だけでも認証情報の解決が走る。ダミーで分離する
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
