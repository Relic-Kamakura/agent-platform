"""評価ハーネス。cases.jsonl の各ケースでエージェントを実行し、judges で判定する。

実行（リポジトリルートから。要 AWS = Bedrock 呼び出しが発生する）:
    uv run --project 07-full-app python 13-evaluation/run_eval.py
    uv run --project 07-full-app python 13-evaluation/run_eval.py --only pricing-comparison

コスト概算を出す場合は 100 万トークンあたりの単価を環境変数で渡す:
    PRICE_IN_PER_MTOK=3.0 PRICE_OUT_PER_MTOK=15.0 uv run --project 07-full-app python 13-evaluation/run_eval.py
（単価はモデルと契約で変わるため、このリポジトリにはハードコードしない）
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

CHAPTER_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(CHAPTER_DIR))          # judges.py
sys.path.insert(0, str(CHAPTER_DIR.parent / "07-full-app"))  # src.*

from judges import judge_case  # noqa: E402

from src.agents.orchestrator import ResearchOrchestrator  # noqa: E402
from src.config import get_settings  # noqa: E402


def load_cases(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="このケース ID だけ実行する")
    args = parser.parse_args()

    cases = load_cases(CHAPTER_DIR / "cases.jsonl")
    if args.only:
        cases = [c for c in cases if c["id"] == args.only]
        if not cases:
            print(f"ケース {args.only!r} が見つかりません", file=sys.stderr)
            return 2

    orchestrator = ResearchOrchestrator(get_settings())
    price_in = float(os.environ.get("PRICE_IN_PER_MTOK", "0"))
    price_out = float(os.environ.get("PRICE_OUT_PER_MTOK", "0"))

    failed_total = 0
    tokens_in_total = tokens_out_total = 0

    for case in cases:
        result = orchestrator.run(case["prompt"])
        tool_calls = orchestrator._guards.tool_limiter.total_calls
        failures = judge_case(
            report=result.report,
            usage=result.usage,
            tool_calls=tool_calls,
            expect=case["expect"],
        )
        tokens_in = result.usage.get("inputTokens", 0)
        tokens_out = result.usage.get("outputTokens", 0)
        tokens_in_total += tokens_in
        tokens_out_total += tokens_out

        status = "PASS" if not failures else "FAIL"
        failed_total += bool(failures)
        print(f"[{status}] {case['id']}  tools={tool_calls}  in={tokens_in} out={tokens_out}")
        for failure in failures:
            print(f"       - {failure}")

    print(f"\n{len(cases) - failed_total}/{len(cases)} passed")
    if price_in and price_out:
        cost = tokens_in_total / 1_000_000 * price_in + tokens_out_total / 1_000_000 * price_out
        print(f"推定コスト: ${cost:.4f} (in={tokens_in_total} out={tokens_out_total} tokens)")
    return 1 if failed_total else 0


if __name__ == "__main__":
    raise SystemExit(main())
