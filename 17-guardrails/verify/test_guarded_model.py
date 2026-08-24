"""演習 17（アプリ側）の合格判定。モデルは呼ばず、組み立ての配線だけを検査する。"""

from __future__ import annotations

import pathlib

import pytest
from strands.models import BedrockModel


def _build(guarded_module, **kwargs) -> BedrockModel:
    model = guarded_module.build_guarded_model(
        model_id="dummy-model-id", region_name="us-east-1", **kwargs
    )
    if not isinstance(model, BedrockModel):
        pytest.fail(
            "build_guarded_model が BedrockModel を返していません。"
            "README 17.4.1 に沿って実装してください。"
        )
    return model


def test_no_todo_left(guarded_module) -> None:
    source = pathlib.Path(guarded_module.__file__).read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/guarded_model.py に TODO が残っています。README 17.4.1 に沿って"
        "実装し、終わったら TODO コメントを消してください。"
    )


def test_guardrail_wired_when_specified(guarded_module) -> None:
    config = _build(
        guarded_module, guardrail_id="gr-test", guardrail_version="1"
    ).get_config()
    assert config.get("guardrail_id") == "gr-test", (
        "guardrail_id が BedrockModel に渡っていません（17.4.1 TODO(1)）。"
    )
    assert config.get("guardrail_version") == "1", (
        "guardrail_version も渡してください。Strands は id と version が両方"
        "揃ったときだけ guardrailConfig を API に送ります（17.2.2）。"
    )


def test_model_uses_arguments(guarded_module) -> None:
    config = _build(
        guarded_module, guardrail_id="gr-test", guardrail_version="1"
    ).get_config()
    assert config.get("model_id") == "dummy-model-id", (
        "model_id は引数の値をそのまま BedrockModel に渡してください（17.4.1 TODO(1)）。"
    )


def test_no_guardrail_when_unspecified(guarded_module) -> None:
    config = _build(guarded_module).get_config()
    assert config.get("guardrail_id") is None, (
        "guardrail_id が未指定のときは接続しないでください（17.4.1 TODO(2)）。"
    )
    assert config.get("guardrail_version") is None, (
        "guardrail_version も渡さないでください（17.4.1 TODO(2)）。"
    )
