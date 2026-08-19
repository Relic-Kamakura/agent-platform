"""役割ごとの Bedrock モデル生成。

モデル ID は必ず Settings 経由で解決する。ここにリテラルを書かない。
"""

from __future__ import annotations

from strands.models import BedrockModel

from ..config import Role, Settings


def build_model(settings: Settings, role: Role) -> BedrockModel:
    return BedrockModel(
        region_name=settings.aws_region,
        model_id=settings.model_id_for(role),
        max_tokens=settings.max_tokens_for(role),
    )
