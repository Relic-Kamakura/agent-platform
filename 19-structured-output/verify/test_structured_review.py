"""第19章の合格判定。構造化出力への置き換えを検査する。"""

from __future__ import annotations

import os
import pathlib
import typing

import pytest

from src.config import Settings


def _app_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("AGENT_APP_DIR", pathlib.Path(__file__).resolve().parents[2] / "07-full-app")
    )


def test_verdict_model_shape() -> None:
    try:
        from src.agents.review_agent import ReviewVerdict
    except ImportError:
        pytest.fail("ReviewVerdict がまだありません。README の 19.3 要件 1 を確認してください。")

    fields = ReviewVerdict.model_fields
    assert set(fields) >= {"verdict", "notes"}, f"verdict と notes が必要です: {set(fields)}"
    hints = typing.get_type_hints(ReviewVerdict)
    assert typing.get_args(hints["verdict"]) == ("ok", "revise"), (
        'verdict は Literal["ok", "revise"] にしてください（スキーマで選択肢を強制する。19.2）。'
    )
    assert fields["verdict"].description, "Field の description に判定基準を書いてください。"


def test_agent_uses_structured_output() -> None:
    from src.agents.review_agent import ReviewAgent, ReviewVerdict

    agent = ReviewAgent(Settings())._agent
    # Strands 内部では _default_structured_output_model に保持される（実機で確認）
    assert getattr(agent, "_default_structured_output_model", None) is ReviewVerdict, (
        "Agent に structured_output_model=ReviewVerdict を渡してください（19.3 要件 2）。"
    )


def test_parser_is_gone() -> None:
    source = (_app_dir() / "src/agents/review_agent.py").read_text(encoding="utf-8")
    assert "_parse_verdict" not in source, "_parse_verdict を削除してください（19.3 要件 5）。"
    assert "VERDICT:" not in source, (
        "システムプロンプトから VERDICT: の形式指定を削ってください。形式はスキーマの仕事です（19.3 要件 3）。"
    )


def test_outcome_mapping_including_none() -> None:
    from src.agents.review_agent import ReviewVerdict, _outcome_from

    ok = _outcome_from(ReviewVerdict(verdict="ok", notes="指摘なし"))
    assert ok.verdict == "ok" and not ok.needs_revision

    revise = _outcome_from(ReviewVerdict(verdict="revise", notes="- 出典が無い"))
    assert revise.needs_revision and "出典" in revise.notes

    fallback = _outcome_from(None)
    assert fallback.needs_revision, (
        "構造化出力が None のときは revise に倒してください。"
        "判定不能を「問題なし」にしない方針は従来と同じです（19.3 要件 4）。"
    )
