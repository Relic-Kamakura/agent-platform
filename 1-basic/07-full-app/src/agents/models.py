"""役割ごとの Bedrock モデル生成。

モデル ID は必ず Settings 経由で解決する。ここにリテラルを書かない。

BedrockModel は boto3 クライアントを内包しており、スレッドセーフなので
リクエスト間で共有してよい。Agent はリクエストごとに作る（orchestrator.py 参照）。
"""

from __future__ import annotations

from botocore.config import Config as BotocoreConfig
from strands.models import BedrockModel

from ..config import Role, Settings


def build_model(settings: Settings, role: Role) -> BedrockModel:
    # Strands の既定は read_timeout=120 秒と botocore 既定の自動リトライ。
    # 長い生成が読み取りタイムアウトで切れると、boto3 が同じリクエストを自動で再送し、
    # 同じ生成が二重に走る（課金も二重）。自動再送は止め、失敗は失敗として返す。
    # 値は .env の BEDROCK_READ_TIMEOUT_SECONDS などで変える。
    boto_config = BotocoreConfig(
        read_timeout=settings.bedrock_read_timeout_seconds,
        connect_timeout=settings.bedrock_connect_timeout_seconds,
        retries={"max_attempts": settings.bedrock_max_attempts, "mode": "standard"},
    )
    return BedrockModel(
        region_name=settings.aws_region,
        model_id=settings.model_id_for(role),
        max_tokens=settings.max_tokens_for(role),
        boto_client_config=boto_config,
    )
