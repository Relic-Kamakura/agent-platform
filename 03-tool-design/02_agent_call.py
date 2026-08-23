"""fetch_page をエージェントに渡し、モデルに選ばせて呼ぶ（編集不要。Bedrock を呼ぶ）。"""

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from strands import Agent
from strands.models import BedrockModel

from fetch_page import build_fetch_page_tool

# モデル ID。第1章 1.3 の手順で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

agent = Agent(
    model=BedrockModel(
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        model_id=MODEL_ID,
        max_tokens=1024,
    ),
    system_prompt="質問に日本語で簡潔に答えてください。",
    tools=[build_fetch_page_tool(timeout_seconds=20.0, max_retries=2)],
)

if __name__ == "__main__":
    agent("https://example.com の内容を 1 行で要約して")
