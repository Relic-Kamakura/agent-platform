"""ハンズオン 2.5: ツールを自分で追加する。

TODO を実装し、`uv run exercises/02_add_tool.py` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/02_add_tool.py。
"""

import os
from datetime import UTC, datetime

from strands import Agent, tool
from strands.models import BedrockModel

MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-sonnet-4-6")


@tool
def now() -> str:
    """現在の日時を UTC の ISO 8601 形式で返す。

    「今日」「現在」など、実行時点の日時が必要な質問に答えるときに使う。

    受け取るもの: なし
    返すもの: ISO 8601 形式の日時文字列 1 つ
    含まないもの: タイムゾーン変換、日付計算
    """
    return datetime.now(UTC).isoformat()


# TODO(1): char_count ツールを実装する。
#   - @tool を付けた char_count(text: str) -> str
#   - docstring に 3 節（受け取るもの / 返すもの / 含まないもの）を必ず書く。
#     含まないものには否定を 1 つ以上入れる（例: 単語数のカウントはしない）
#   - 返り値は文字数を含む短い文字列（例: "7 文字"）


# TODO(2): Agent を組み立てる。tools に now と char_count の両方を渡し、
#   system_prompt でそれぞれの使いどころを 1 文ずつ伝える
agent = ...

if __name__ == "__main__":
    # TODO(3): 「『こんにちは世界』は何文字？」と質問し、cycle_count を表示する
    ...
