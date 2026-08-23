"""ストリーミング呼び出し。最初のチャンクまでの時間と合計時間を実測する。"""

import os
import time

import boto3

client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
model_id = os.environ.get("MODEL_ID", "us.anthropic.claude-sonnet-4-6")

start = time.perf_counter()
first_token_at = None
usage = None

# converse ではなく converse_stream。引数は同じ
response = client.converse_stream(
    modelId=model_id,
    messages=[
        {"role": "user", "content": [{"text": "エージェント開発を学ぶ手順を詳しく説明して"}]},
    ],
    inferenceConfig={"maxTokens": 500},
)

for event in response["stream"]:
    if "contentBlockDelta" in event:
        if first_token_at is None:
            first_token_at = time.perf_counter() - start
        print(event["contentBlockDelta"]["delta"]["text"], end="", flush=True)
    elif "metadata" in event:
        # 消費トークンは最後の metadata イベントに入る
        usage = event["metadata"]["usage"]

total = time.perf_counter() - start
print(f"\n\nfirst_token={first_token_at:.2f}s total={total:.2f}s")
print(f"tokens: in={usage['inputTokens']} out={usage['outputTokens']}")
