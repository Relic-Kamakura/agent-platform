"""ハンズオン 1.4: Converse API を直接呼ぶ。

TODO を実装し、`uv run exercises/01_converse.py` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/01_converse.py。
"""

import os

import boto3

# Bedrock Runtime を呼び出すクライアントを生成
client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# モデル ID。地理接頭辞の意味は README 1.1.6 参照。
# 1.3 の一覧に無い場合は、この既定値を書き換えるか環境変数 MODEL_ID で上書きする
model_id = os.environ.get("MODEL_ID", "us.anthropic.claude-sonnet-4-6")

# TODO(1): client.converse を呼ぶ。
#   - modelId に model_id を渡す
#   - messages に「こんにちは。1 行で自己紹介して」という user メッセージを 1 件入れる
#     （形式は README 1.1.3。content は {"text": ...} のリスト）
#   - inferenceConfig で maxTokens を 300 に制限する
response = ...

# TODO(2): 応答テキストを表示する。
#   本文は response["output"]["message"]["content"] の先頭要素の "text" に入っている
print(...)

# TODO(3): 消費トークンを表示する。response["usage"] に入っている
usage = ...
print(f"tokens: in={usage['inputTokens']} out={usage['outputTokens']}")
