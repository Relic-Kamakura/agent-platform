"""ハンズオン 2.3: 最小のエージェントを書く。

TODO を実装し、`uv run exercises/01_agent.py` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/01_agent.py。
"""

import os
from datetime import UTC, datetime

from strands import Agent, tool
from strands.models import BedrockModel

# モデル ID。第1章 1.3 の手順で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")


@tool
def now() -> str:
    """現在の日時を UTC の ISO 8601 形式で返す。

    「今日」「現在」など、実行時点の日時が必要な質問に答えるときに使う。

    受け取るもの: なし
    返すもの: ISO 8601 形式の日時文字列 1 つ
    含まないもの: タイムゾーン変換、日付計算
    """
    return datetime.now(UTC).isoformat()


# TODO(1): Agent を組み立てる。
#   - model には BedrockModel。region_name は環境変数 AWS_REGION（既定 us-east-1）、
#     model_id は MODEL_ID、max_tokens は 512
#   - system_prompt は「質問に日本語で簡潔に答えてください。日時が必要なら now ツールを使ってください。」
#   - tools に [now] を渡す（渡した関数の docstring がそのままモデルに渡る）
agent = ...

if __name__ == "__main__":
    result = agent("今日は何日ですか？")
    # TODO(2): ループが何周したかを表示する。result.metrics.cycle_count に入っている
    print(...)
