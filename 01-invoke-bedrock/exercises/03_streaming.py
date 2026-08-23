"""ハンズオン 1.6: ストリーミング呼び出し。最初のチャンクまでの時間を実測する。

TODO を実装し、`uv run exercises/03_streaming.py` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/03_streaming.py。
"""

import os
import time

import boto3

client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
model_id = os.environ.get("MODEL_ID", "us.anthropic.claude-sonnet-4-6")

start = time.perf_counter()
first_token_at = None
usage = None

# TODO(1): converse ではなく converse_stream で呼ぶ。引数は converse と同じ。
#   質問は 1.5 の 3 つ目と同じ「エージェント開発を学ぶ手順を詳しく説明して」、
#   maxTokens は 500 にする
response = ...

for event in response["stream"]:
    # TODO(2): contentBlockDelta イベントが来たら、そのテキスト
    #   （event["contentBlockDelta"]["delta"]["text"]）を print(..., end="", flush=True) で
    #   逐次表示する。最初のチャンクだった場合は経過時間を first_token_at に記録する
    # TODO(3): metadata イベントが来たら usage（event["metadata"]["usage"]）を取り出す
    ...

total = time.perf_counter() - start
print(f"\n\nfirst_token={first_token_at:.2f}s total={total:.2f}s")
print(f"tokens: in={usage['inputTokens']} out={usage['outputTokens']}")
