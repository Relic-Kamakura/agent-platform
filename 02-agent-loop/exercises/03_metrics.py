"""ハンズオン 2.6: ツールが要る質問と要らない質問のコスト差を見る。

TODO を実装し、`uv run exercises/03_metrics.py` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/03_metrics.py。
"""

from importlib import import_module

mod = import_module("02_add_tool")
agent = mod.agent

for question in ("こんにちは", "今日は何日？『こんにちは世界』は何文字？"):
    result = agent(question)
    # TODO(1): この質問の cycle 数とトークン合計を表示する。
    #   何周したかは result.metrics.cycle_count、
    #   トークン累計は result.metrics.accumulated_usage（dict。合計はキー totalTokens）
    print(...)
