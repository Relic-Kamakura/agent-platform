"""同じエージェントで、ツールが要る質問と要らない質問のコスト差を見る。"""

from importlib import import_module

mod = import_module("02_add_tool")
agent = mod.agent

for question in ("こんにちは", "今日は何日？『こんにちは世界』は何文字？"):
    result = agent(question)
    usage = result.metrics.accumulated_usage
    print(f"\nQ: {question}")
    print(f"  cycles={result.metrics.cycle_count}  tokens={usage.get('totalTokens')}")
