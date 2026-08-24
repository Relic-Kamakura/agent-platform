"""演習 19 の合格判定。パース版の故障モードと、構造化出力版の挙動を検査する（完全オフライン）。"""

from __future__ import annotations

import pathlib
import typing
from types import SimpleNamespace


class _StubAgent:
    """structured_output をスタブ化したダミーエージェント。モデルを呼ばずに検証する。"""

    def __init__(self, structured_output) -> None:
        self._structured_output = structured_output
        self.received_prompt: str | None = None
        self.received_model = None

    def __call__(self, prompt, structured_output_model=None, **kwargs):
        self.received_prompt = prompt
        self.received_model = structured_output_model
        return SimpleNamespace(structured_output=self._structured_output)


class _RaisingAgent:
    def __call__(self, prompt, structured_output_model=None, **kwargs):
        raise RuntimeError("model unavailable")


def test_no_todo_left(review_module) -> None:
    source = pathlib.Path(review_module.__file__).read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/review.py に TODO が残っています。README 19.3 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


def test_verdict_model_shape(review_module) -> None:
    fields = review_module.Verdict.model_fields
    assert set(fields) >= {"verdict", "reasons"}, f"verdict と reasons が必要です: {set(fields)}"
    hints = typing.get_type_hints(review_module.Verdict)
    assert typing.get_args(hints["verdict"]) == ("approve", "revise"), (
        'verdict は Literal["approve", "revise"] にしてください（スキーマで選択肢を強制する。19.2）。'
    )
    assert hints["reasons"] == list[str], "reasons は list[str] にしてください。"


def test_parser_reads_promised_format(review_module) -> None:
    verdict = review_module.parse_verdict_text("VERDICT: approve\n指摘なし")
    assert verdict.verdict == "approve"


def test_parser_misjudges_broken_input(review_module) -> None:
    # どちらも書き手は approve のつもり。形式が約束と違うだけで revise に化ける
    preamble = review_module.parse_verdict_text("報告を確認しました。結論は以下です。\nVERDICT: approve")
    assert preamble.verdict == "revise", (
        "この誤判定こそがテキストパースの故障モードです（README 19.1.2）。"
        "パーサを直すのではなく、structured_verdict で消します。"
    )
    paraphrased = review_module.parse_verdict_text("判定: approve\n指摘なし")
    assert paraphrased.verdict == "revise"


def test_structured_verdict_returns_validated_instance(review_module) -> None:
    expected = review_module.Verdict(verdict="approve", reasons=[])
    agent = _StubAgent(structured_output=expected)
    got = review_module.structured_verdict(agent, "検証対象の報告本文")
    assert got is expected, (
        "result.structured_output の Verdict をそのまま返してください（README 19.3）。"
    )
    assert agent.received_model is review_module.Verdict, (
        "呼び出しに structured_output_model=Verdict を渡してください。"
    )
    assert agent.received_prompt and "検証対象の報告本文" in agent.received_prompt, (
        "report をプロンプトに含めてください。モデルは渡されたものしか検証できません。"
    )


def test_structured_verdict_falls_back_to_revise_on_error(review_module) -> None:
    got = review_module.structured_verdict(_RaisingAgent(), "報告本文")
    assert got.verdict == "revise", (
        "呼び出しが例外を投げたら revise の Verdict を返してください。"
        "判定不能を「問題なし」にしたら検証機構として意味をなしません（README 19.2.2）。"
    )
    assert got.reasons, "reasons に判定を取得できなかった旨を書いてください。"


def test_structured_verdict_falls_back_to_revise_on_none(review_module) -> None:
    got = review_module.structured_verdict(_StubAgent(structured_output=None), "報告本文")
    assert got.verdict == "revise", (
        "structured_output が None のときも revise の Verdict を返してください（README 19.2.2）。"
    )
