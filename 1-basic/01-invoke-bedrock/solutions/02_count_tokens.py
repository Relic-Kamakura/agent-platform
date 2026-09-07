"""質問の長さを変えて、トークン数と料金の関係を実測する。"""

import os

import boto3

# Bedrock 料金ページの単価（USD / 100万トークン）。モデルとリージョンに合わせて直す
PRICE_INPUT = 1.00
PRICE_OUTPUT = 5.00

client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
model_id = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")


def ask(text: str) -> None:
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": text}]}],
        inferenceConfig={"maxTokens": 500},
    )
    usage = response["usage"]
    cost = usage["inputTokens"] * PRICE_INPUT / 1_000_000 + usage["outputTokens"] * PRICE_OUTPUT / 1_000_000
    print(f"in={usage['inputTokens']:4} out={usage['outputTokens']:4} cost=${cost:.6f} <- {text}")


ask("1+1 は？答えだけ")
ask("エージェント開発を学ぶ手順を 3 項目で")
ask("エージェント開発を学ぶ手順を詳しく説明して")
