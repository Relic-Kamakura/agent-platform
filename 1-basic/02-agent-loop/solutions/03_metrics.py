"""ツールが要る質問と要らない質問のコスト差を見る。"""

from importlib import import_module

build_agent = import_module("02_add_tool").build_agent

for question in ("こんにちは", "今日は何日？『こんにちは世界』は何文字？"):
    # メトリクスも会話履歴も Agent の生涯で累積するので、質問ごとに作り直す
    agent = build_agent()
    result = agent(question)
    usage = result.metrics.accumulated_usage
    print(f"\nQ: {question}")
    print(f"  cycles={result.metrics.cycle_count}  tokens={usage.get('totalTokens')}")
