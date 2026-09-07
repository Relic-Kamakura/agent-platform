"""第1章の合格判定。exercises/ のスクリプトが完成しているかを検査する。"""

from __future__ import annotations

import ast
import pathlib

EXERCISES = pathlib.Path(__file__).resolve().parents[1] / "exercises"


def _completed_source(name: str, section: str) -> str:
    path = EXERCISES / name
    assert path.exists(), f"exercises/{name} がありません。README {section} を読み直してください。"
    source = path.read_text(encoding="utf-8")
    assert "TODO" not in source, (
        f"exercises/{name} に TODO が残っています。README {section} に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )
    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise AssertionError(f"exercises/{name} が Python として不正です: {exc}") from exc
    return source


def test_converse_script() -> None:
    source = _completed_source("01_converse.py", "1.4")
    assert "client.converse" in source, "01_converse.py で client.converse(...) を呼んでください。"
    assert "usage" in source, "01_converse.py で消費トークン（response['usage']）も表示してください。"


def test_count_tokens_script() -> None:
    source = _completed_source("02_count_tokens.py", "1.5")
    assert "PRICE_INPUT" in source and "PRICE_OUTPUT" in source, (
        "02_count_tokens.py で入力・出力それぞれの単価から料金を計算してください（README 1.5）。"
    )
    assert source.count("ask(") >= 3, (
        "02_count_tokens.py で長さの違う 3 つの質問を投げてください（README 1.5）。"
    )


def test_streaming_script() -> None:
    source = _completed_source("03_streaming.py", "1.6")
    assert "converse_stream" in source, "03_streaming.py では client.converse_stream(...) を使ってください。"
    assert "contentBlockDelta" in source, (
        "03_streaming.py でストリームの contentBlockDelta からテキストを取り出してください（README 1.6）。"
    )
    assert "metadata" in source, (
        "03_streaming.py で metadata イベントから usage を取り出してください（README 1.6）。"
    )
