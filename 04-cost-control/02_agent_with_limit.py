"""CostLimiter を実エージェントに付けて、上限で止まる様子を観察する（編集不要。Bedrock を呼ぶ）。"""

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from strands import Agent, tool
from strands.models import BedrockModel

from cost_limiter import CostLimiter

# モデル ID。第1章 1.3 の手順で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")


@tool
def lookup(topic: str) -> str:
    """社内メモから topic に関する記述を探して返す。

    受け取るもの: topic。調べたい語をひとつだけ渡す。
    返すもの: 見つかったメモの本文（長文）。
    含まないもの: 要約。本文をそのまま返す。
    """
    # 意図的に長い本文を返し、ターンごとに履歴（= 次の入力）を長くする
    return f"{topic} に関するメモ: " + f"{topic} の事業と沿革についての記述。" * 200


limiter = CostLimiter(max_total_tokens=6_000)

agent = Agent(
    model=BedrockModel(
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        model_id=MODEL_ID,
        max_tokens=1024,
    ),
    system_prompt="質問に日本語で簡潔に答えてください。調べ物には lookup を使ってください。",
    tools=[lookup],
    hooks=[limiter],
)

if __name__ == "__main__":
    result = agent("A社、B社、C社の 3 つを順番に lookup で調べて、それぞれ 1 行で紹介して")
    usage = result.metrics.accumulated_usage
    print(f"\ncycles: {result.metrics.cycle_count}  tokens: {usage.get('totalTokens')}")
