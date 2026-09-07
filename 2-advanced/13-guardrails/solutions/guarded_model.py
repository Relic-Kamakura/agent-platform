"""第17章の模範解答。exercises/guarded_model.py の完成形。"""

from __future__ import annotations

from strands.models import BedrockModel


def build_guarded_model(
    model_id: str,
    region_name: str,
    guardrail_id: str | None = None,
    guardrail_version: str | None = None,
) -> BedrockModel:
    """Guardrail の指定があるときだけ接続した BedrockModel を組み立てる。"""
    if guardrail_id and guardrail_version:
        return BedrockModel(
            region_name=region_name,
            model_id=model_id,
            guardrail_id=guardrail_id,
            guardrail_version=guardrail_version,
        )
    # 未設定なら接続しない。どの Guardrail を使うかはコードに書かず、
    # 環境変数から受け取る（リージョンやモデル ID と同じ扱い）
    return BedrockModel(region_name=region_name, model_id=model_id)
