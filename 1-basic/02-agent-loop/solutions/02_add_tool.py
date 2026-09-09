import os
from datetime import UTC, datetime

from strands import Agent, tool
from strands.models import BedrockModel

# モデル ID。aws bedrock list-inference-profiles で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")


@tool
def now() -> str:
    """現在の日時を UTC の ISO 8601 形式で返す。

    「今日」「現在」など、実行時点の日時が必要な質問に答えるときに使う。

    受け取るもの: なし
    返すもの: ISO 8601 形式の日時文字列 1 つ
    含まないもの: タイムゾーン変換、日付計算
    """
    return datetime.now(UTC).isoformat()


@tool
def char_count(text: str) -> str:
    """文字列の文字数を数えて返す。

    「何文字？」のように、正確な文字数が必要な質問に答えるときに使う。
    モデル自身の文字数カウントは間違えることがあるため、必ずこのツールを使うこと。

    受け取るもの:
        text: 数えたい文字列そのもの。前後の説明文を含めずに渡すこと。
    返すもの:
        文字数を含む短い文字列（例: "7 文字"）。
    含まないもの:
        単語数・バイト数のカウント。空白や記号も 1 文字として数える。
    """
    return f"{len(text)} 文字"


def build_agent() -> Agent:
    """エージェントを 1 つ組み立てて返す。

    メトリクスと会話履歴は Agent インスタンスの生涯で累積するので、
    1 回の呼び出しぶんを見たいときは毎回この関数で作り直す（2.5）。
    """
    return Agent(
        model=BedrockModel(
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            model_id=MODEL_ID,
            max_tokens=512,
        ),
        system_prompt="質問に日本語で簡潔に答えてください。日時は now、文字数は char_count を使ってください。",
        tools=[now, char_count],
    )


if __name__ == "__main__":
    result = build_agent()("『こんにちは世界』は何文字？")
    print(f"\ncycles: {result.metrics.cycle_count}")
