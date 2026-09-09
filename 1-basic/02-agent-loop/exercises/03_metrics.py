"""ハンズオン 2.5: ツールが要る質問と要らない質問のコスト差を見る。

TODO を実装し、`uv run exercises/03_metrics.py` で実行する。
実装が終わったら TODO コメントは消す。完成形は solutions/03_metrics.py。
"""

from importlib import import_module

build_agent = import_module("02_add_tool").build_agent

for question in ("こんにちは", "今日は何日？『こんにちは世界』は何文字？"):
    # メトリクスも会話履歴も Agent の生涯で累積するので、質問ごとに作り直す
    agent = build_agent()
    result = agent(question)
    # TODO(1): この質問の cycle 数とトークン合計を表示する。
    #   何周したかは result.metrics.cycle_count、
    #   トークン量は result.metrics.accumulated_usage（dict。合計はキー totalTokens）
    print(...)
