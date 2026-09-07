import os

import boto3

# Bedrock Runtime を呼び出すクライアントを生成
client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# モデル ID。地理接頭辞の意味は README 1.1.7 参照。
# 1.3 の一覧に無い場合は、この既定値を書き換えるか環境変数 MODEL_ID で上書きする
model_id = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

# Converse API 呼び出し
response = client.converse(
    modelId=model_id,
    messages=[
        {"role": "user", "content": [{"text": "こんにちは。1 行で自己紹介して"}]},
    ],
    inferenceConfig={"maxTokens": 300},
)

# 応答テキストを表示
print(response["output"]["message"]["content"][0]["text"])

# 消費トークン。第4章のコスト計測はこの値の積み上げ
usage = response["usage"]
print(f"tokens: in={usage['inputTokens']} out={usage['outputTokens']}")
