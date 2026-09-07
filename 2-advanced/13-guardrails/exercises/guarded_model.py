"""ハンズオン 17.4: Guardrail 付きモデルの組み立て。

TODO を実装し、`uv run pytest -q` で判定する。
実装が終わったら TODO コメントは消す。完成形は solutions/guarded_model.py。
"""

from __future__ import annotations

from strands.models import BedrockModel


def build_guarded_model(
    model_id: str,
    region_name: str,
    guardrail_id: str | None = None,
    guardrail_version: str | None = None,
) -> BedrockModel:
    """Guardrail の指定があるときだけ接続した BedrockModel を組み立てる。"""
    # TODO(1): guardrail_id と guardrail_version の両方が指定されているときは、
    #   BedrockModel に guardrail_id / guardrail_version を渡して返す。
    #   region_name と model_id は引数の値をそのまま渡す
    # TODO(2): どちらかが None のときは guardrail_* を渡さずに返す（接続しない）。
    #   Strands は両方が揃ったときだけ guardrailConfig を API に送るため、
    #   片方だけ渡した中途半端な状態を作らない
    ...
