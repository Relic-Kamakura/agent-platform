import os
from datetime import UTC, datetime

from strands import Agent, tool
from strands.models import BedrockModel

# モデル ID の解決規則は第1章で実装したとおり。
# 自分のリージョンで呼べる ID に合わせて MODEL_ID を設定する
MODEL_ID = os.environ.get("MODEL_ID", "apac.anthropic.claude-haiku-4-5")


@tool
def now() -> str:
    """現在の日時を UTC の ISO 8601 形式で返す。

    「今日」「現在」など、実行時点の日時が必要な質問に答えるときに使う。

    受け取るもの: なし
    返すもの: ISO 8601 形式の日時文字列 1 つ
    含まないもの: タイムゾーン変換、日付計算
    """
    return datetime.now(UTC).isoformat()


# エージェント本体。tools に渡した関数の docstring がモデルに渡る
agent = Agent(
    model=BedrockModel(
        region_name=os.environ.get("AWS_REGION", "ap-northeast-1"),
        model_id=MODEL_ID,
        max_tokens=512,
    ),
    system_prompt="質問に日本語で簡潔に答えてください。日時が必要なら now ツールを使ってください。",
    tools=[now],
)

if __name__ == "__main__":
    result = agent("今日は何日ですか？")
    # ループが何周したか。ツールを 1 回使う質問なら 2 になるはず
    print(f"\ncycles: {result.metrics.cycle_count}")
