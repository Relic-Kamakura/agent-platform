"""第13章の模範解答。13-evaluation/judges.py として配置する。

ルールベースの判定関数群。各関数は「失敗メッセージのリスト」を返す（空 = 合格）。
真偽値でなくメッセージを返すのは、FAIL の理由がそのままレポートに出るようにするため。
"""

from __future__ import annotations


def judge_contains(report: str, terms: list[str]) -> list[str]:
    """含むべき語。事実の取りこぼしを検出する。"""
    return [f"含むべき語が無い: {term!r}" for term in terms if term not in report]


def judge_not_contains(report: str, terms: list[str]) -> list[str]:
    """含んではいけない語。でっち上げ・禁止表現を検出する。"""
    return [f"含んではいけない語がある: {term!r}" for term in terms if term in report]


def judge_source(report: str) -> list[str]:
    """出典 URL の有無。出典の無い報告は検証できない。"""
    if "http://" in report or "https://" in report:
        return []
    return ["出典 URL が 1 つも無い"]


def judge_tool_calls(tool_calls: int, limit: int) -> list[str]:
    """ツール呼び出し数の上限。調査の暴走・非効率を検出する。"""
    if tool_calls <= limit:
        return []
    return [f"ツール呼び出しが多すぎる: {tool_calls} > {limit}"]


def judge_tokens(usage: dict, limit: int) -> list[str]:
    """トークン消費の上限。コスト退行を検出する。"""
    total = usage.get("totalTokens", 0)
    if total <= limit:
        return []
    return [f"トークン消費が多すぎる: {total} > {limit}"]


def judge_case(report: str, usage: dict, tool_calls: int, expect: dict) -> list[str]:
    """1 ケース分の判定。expect に書かれたルールだけを適用する。"""
    failures: list[str] = []
    if "contains" in expect:
        failures += judge_contains(report, expect["contains"])
    if "not_contains" in expect:
        failures += judge_not_contains(report, expect["not_contains"])
    if expect.get("require_source"):
        failures += judge_source(report)
    if "max_tool_calls" in expect:
        failures += judge_tool_calls(tool_calls, expect["max_tool_calls"])
    if "max_total_tokens" in expect:
        failures += judge_tokens(usage, expect["max_total_tokens"])
    return failures
