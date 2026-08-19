"""第12章の合格判定。judges の挙動と、自作ケースの追加を検査する（AWS 不要）。"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAPTER_DIR))

try:
    from judges import judge_case
except ModuleNotFoundError:
    pytest.fail(
        "12-evaluation/judges.py がまだありません。README の 12.3 に沿って書いてください。",
        pytrace=False,
    )

BASE_IDS = {"pricing-comparison", "feature-survey", "unknown-topic-honesty"}


def test_contains_and_not_contains() -> None:
    report = "Acme は月額 49 ドル。出典: https://example.com"
    ok = judge_case(report, usage={}, tool_calls=0, expect={"contains": ["49"]})
    assert ok == [], f"合格すべきケースが失敗: {ok}"

    failures = judge_case(report, usage={}, tool_calls=0, expect={"contains": ["99"]})
    assert failures and "99" in failures[0], "含むべき語の欠落を検出できていません。"

    failures = judge_case(report, usage={}, tool_calls=0, expect={"not_contains": ["49"]})
    assert failures, "含んではいけない語を検出できていません。"


def test_source_rule() -> None:
    assert judge_case("出典なしの報告", {}, 0, {"require_source": True}), (
        "出典 URL 無しを検出できていません。"
    )
    assert judge_case("出典: https://e.com", {}, 0, {"require_source": True}) == []


def test_limits() -> None:
    failures = judge_case("r", usage={"totalTokens": 50_000}, tool_calls=9,
                          expect={"max_tool_calls": 8, "max_total_tokens": 30_000})
    assert len(failures) == 2, f"ツール数とトークンの両方の超過を検出すべきです: {failures}"


def test_failures_are_messages_not_bools() -> None:
    failures = judge_case("r", {}, 0, {"contains": ["x"]})
    assert all(isinstance(f, str) and len(f) > 5 for f in failures), (
        "判定は bool ではなく、理由が読める文字列で返してください（12.3 の設計方針）。"
    )


def test_learner_added_cases() -> None:
    cases = [
        json.loads(line)
        for line in (CHAPTER_DIR / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids)), "ケース ID が重複しています。"
    added = [case for case in cases if case["id"] not in BASE_IDS]
    assert len(added) >= 2, (
        f"自作ケースを 2 件以上追加してください（12.4）。現在の追加数: {len(added)}"
    )
    for case in added:
        assert case.get("prompt"), f"{case['id']}: prompt が空です。"
        assert case.get("expect"), f"{case['id']}: expect がありません。"
        assert any(k in case["expect"] for k in
                   ("contains", "not_contains", "require_source", "max_tool_calls", "max_total_tokens")), (
            f"{case['id']}: expect に判定ルールが 1 つもありません。"
        )
