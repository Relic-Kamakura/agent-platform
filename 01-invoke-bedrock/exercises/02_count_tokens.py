"""ハンズオン 1.5: 質問の長さを変えて、トークン数と料金の関係を実測する。

TODO を実装し、`uv run exercises/02_count_tokens.py` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/02_count_tokens.py。
"""

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
    # TODO(1): 1 回分の料金を計算する。
    #   入力トークン数 × PRICE_INPUT + 出力トークン数 × PRICE_OUTPUT。
    #   単価は 100万トークンあたりなので 1_000_000 で割ること
    cost = ...
    print(f"in={usage['inputTokens']:4} out={usage['outputTokens']:4} cost=${cost:.6f} <- {text}")


# TODO(2): 長さの違う 3 つの質問で呼ぶ。
#   答えが一語で済むものから、長い説明を求めるものまで差をつける。
#   出力トークン数の差が、そのまま料金の差になる
ask("1+1 は？答えだけ")
ask(...)
ask(...)
