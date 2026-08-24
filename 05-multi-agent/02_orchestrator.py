"""compare_pricing をオーケストレータに載せて呼ぶ（編集不要。Bedrock を呼ぶ）。"""

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from strands import Agent
from strands.models import BedrockModel

from specialist import build_specialist_tool
from tool_call_limiter import ToolCallLimiter

# モデル ID。第1章 1.3 の手順で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

orchestrator = Agent(
    model=BedrockModel(
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        model_id=MODEL_ID,
        max_tokens=1024,
    ),
    system_prompt=(
        "質問に日本語で簡潔に答えてください。"
        "価格の比較が求められたら compare_pricing を使ってください。"
    ),
    tools=[build_specialist_tool()],
    hooks=[ToolCallLimiter(max_calls=4)],  # オーケストレータ自身にもガードを付ける
)

if __name__ == "__main__":
    result = orchestrator("Acme Analytics と Globex Insights の価格を比較して")
    usage = result.metrics.accumulated_usage
    print(f"\ncycles: {result.metrics.cycle_count}  tokens: {usage.get('totalTokens')}")
