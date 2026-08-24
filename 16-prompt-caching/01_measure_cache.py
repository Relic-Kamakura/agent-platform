"""同じ質問を 2 回投げ、キャッシュ関連のトークン数を比べる（編集不要。Bedrock を呼ぶ）。"""

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from cached_agent import build_cached_agent

# モデル ID。第1章 1.3 の手順で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

QUESTION = "セマンティックレイヤーとは何ですか。用語集の定義に沿って 1 文で答えてください。"


def ask(label: str) -> None:
    # 毎回新しいエージェントで呼ぶ。会話履歴の差をなくし、
    # 1 回目と 2 回目の違いがモデル側のキャッシュだけになるようにする
    agent = build_cached_agent(model_id=MODEL_ID, region_name=REGION)
    result = agent(QUESTION)
    usage = result.metrics.accumulated_usage
    print(f"\n--- {label} ---")
    print(f"inputTokens          : {usage.get('inputTokens', 0)}")
    print(f"cacheWriteInputTokens: {usage.get('cacheWriteInputTokens', 0)}")
    print(f"cacheReadInputTokens : {usage.get('cacheReadInputTokens', 0)}")


if __name__ == "__main__":
    ask("1 回目")
    ask("2 回目")
