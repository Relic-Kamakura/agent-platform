"""第1章の合格判定。学習者が書いた 02_inference_profile.py を検査する。"""

from __future__ import annotations

import pathlib

import pytest

try:
    from importlib import import_module

    impl = import_module("02_inference_profile")
except ModuleNotFoundError:
    pytest.fail(
        "02_inference_profile.py がまだありません。README の 1.5 に沿って作成してください。",
        pytrace=False,
    )


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("ap-northeast-1", "apac"),
        ("ap-southeast-2", "apac"),
        ("us-east-1", "us"),
        ("eu-central-1", "eu"),
        ("us-gov-east-1", "us-gov"),
    ],
)
def test_derive_prefix(region: str, expected: str) -> None:
    assert impl.derive_prefix(region) == expected, (
        f"derive_prefix({region!r}) が {expected!r} になりません。"
        "README 1.5 のヒント（末尾 2 要素を落とす・補正表を通す）を読み直してください。"
    )


def test_resolve_priority() -> None:
    base = "anthropic.claude-haiku-4-5"
    # region からの導出
    assert impl.resolve_model_id(base, "ap-northeast-1") == f"apac.{base}"
    # prefix 明示が導出より優先
    assert impl.resolve_model_id(base, "ap-northeast-1", prefix="us") == f"us.{base}"
    # 空文字 prefix = 接頭辞なし
    assert impl.resolve_model_id(base, "ap-northeast-1", prefix="") == base
    # full は連結せずそのまま
    assert impl.resolve_model_id(base, "us-east-1", full="global.anthropic.claude-x") == (
        "global.anthropic.claude-x"
    )


def test_converse_script_exists() -> None:
    path = pathlib.Path(__file__).resolve().parents[1] / "01_converse.py"
    assert path.exists(), "01_converse.py がありません。README 1.4 の写経から始めてください。"
    source = path.read_text(encoding="utf-8")
    assert "converse" in source, "01_converse.py で client.converse(...) を呼んでください。"
    assert "usage" in source, "01_converse.py で消費トークン（response['usage']）も表示してください。"
