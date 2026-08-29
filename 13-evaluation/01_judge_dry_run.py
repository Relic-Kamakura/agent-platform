"""判定関数に見本の報告を手で渡し、失敗メッセージの出方を見る（編集不要）。

モデルは呼ばない。実行はリポジトリルートから:
    uv run --project 07-full-app python 13-evaluation/01_judge_dry_run.py
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

try:
    from judges import judge_case
except ModuleNotFoundError:
    print("13-evaluation/judges.py がありません。exercises/judges.py を章直下にコピーしてください（README 13.3.1）。")
    sys.exit(1)

# pricing-comparison ケースと同じ期待条件
EXPECT = {
    "contains": ["49", "99"],
    "require_source": True,
    "max_tool_calls": 8,
    "max_total_tokens": 30_000,
}

GOOD_REPORT = (
    "Acme は月額 49 ドル、Globex は月額 99 ドル。\n出典: https://example.com/acme/pricing"
)
BAD_REPORT = "Acme は月額 49 ドルで、Globex より安い。"


def show(name: str, report: str, usage: dict, tool_calls: int) -> None:
    failures = judge_case(report=report, usage=usage, tool_calls=tool_calls, expect=EXPECT)
    if not isinstance(failures, list):
        print("judge_case がリストを返していません。TODO(5) を実装してください（README 13.3.2）。")
        sys.exit(1)
    status = "PASS" if not failures else "FAIL"
    print(f"[{status}] {name}  tools={tool_calls}  total={usage['totalTokens']}")
    for failure in failures:
        print(f"       - {failure}")


show("good-report", GOOD_REPORT, usage={"totalTokens": 12_000}, tool_calls=3)
show("bad-report", BAD_REPORT, usage={"totalTokens": 42_000}, tool_calls=9)
