"""ハンズオン 5.3: 価格調査の専門エージェントをツール化する。

TODO を実装し、`uv run 01_show_tool_spec.py` で動かす。
実装が終わったら TODO コメントは消す。完成形は solutions/specialist.py。
"""

from __future__ import annotations

import os

from strands import Agent, tool
from strands.models import BedrockModel

from tool_call_limiter import ToolCallLimiter

# モデル ID。第1章 1.3 の手順で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

# 専門エージェントが検索する固定データ。実案件では外部 API や DB になる部分
PRICING_DATA = {
    "Acme Analytics": {"Free": "$0", "Pro": "$29/月", "Enterprise": "要問い合わせ"},
    "Globex Insights": {"Starter": "$19/月", "Business": "$99/月"},
    "Initech Data": {"Basic": "$15/月", "Premium": "$60/月", "Enterprise": "$300/月"},
}

SYSTEM_PROMPT = """\
あなたは競合リサーチの価格調査担当です。指定された企業の料金プランを
lookup_pricing で 1 社ずつ調べ、Markdown の比較表にまとめます。

守ること:
- lookup_pricing で確認していない価格を書かない。
- データに無い企業やプランのセルは「不明」とする。推測で埋めない。
- 価格以外の情報（機能、評判）は書かない。
"""


@tool
def lookup_pricing(company: str) -> str:
    """指定した企業の料金プラン一覧を価格データベースから引いて返す。

    企業の価格情報が必要になったときに使う。

    受け取るもの:
        company: 企業名をひとつだけ渡す。複数をまとめて渡さないこと。

    返すもの:
        「プラン名: 価格」を 1 行 1 プランで並べたテキスト。
        企業がデータベースに無い場合は "ERROR[" で始まる文字列。

    含まないもの:
        - 価格以外の情報（機能、評判）。
        - 比較や表への整形。整形はあなたの仕事。
    """
    if company not in PRICING_DATA:
        return (
            f"ERROR[NotFound]: {company} は価格データベースにありません。\n"
            "retryable: no\n"
            "next_action: この企業の価格は「不明」として表に載せてください。"
        )
    return "\n".join(f"{plan}: {price}" for plan, price in PRICING_DATA[company].items())


def build_specialist_agent() -> Agent:
    """価格調査の専門エージェントを組み立てて返す。"""
    # TODO(1): Agent を組み立てて返す。
    #   - model: BedrockModel(region_name=os.environ.get("AWS_REGION", "us-east-1"),
    #                         model_id=MODEL_ID, max_tokens=1024)
    #     価格の検索と表への整形は定型処理なので、軽量モデル（Haiku）で足りる
    #   - system_prompt: SYSTEM_PROMPT
    #   - tools: [lookup_pricing]
    #   - hooks: [ToolCallLimiter(max_calls=4)]  # ガードなしのエージェントを新設しない
    #   - callback_handler=None（専門エージェントの途中経過を呼び出し側の出力に混ぜない）
    ...


def build_specialist_tool():
    """専門エージェントをツールとして返す。オーケストレータはこれを tools に載せる。"""
    agent = build_specialist_agent()

    @tool
    def compare_pricing(companies: str) -> str:
        """TODO(2): docstring を第3章の 3 節構成で書く（3.2.1 参照）。

        使い方の制約（カンマ区切りで 2 社以上）と、このツールが価格以外を
        調べないことまで、docstring がオーケストレータのモデルに教える。
        """
        # TODO(3): agent に「次の企業の価格を比較してください: {companies}」を渡し、
        #   結果を str(...) で文字列にして返す
        ...

    return compare_pricing
