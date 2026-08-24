"""CostLimiter にイベントを手で流し、止まる瞬間と理由を見る（編集不要）。"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from strands.hooks import BeforeInvocationEvent, BeforeModelCallEvent, HookRegistry

from cost_limiter import CostLimiter

limiter = CostLimiter(max_total_tokens=10_000)
registry = HookRegistry()
limiter.register_hooks(registry)

# リクエスト開始。積算がリセットされる
registry.invoke_callbacks(BeforeInvocationEvent(agent=None, invocation_state={}))

# 毎ターン 4,000 トークンの入力が来る想定でモデル呼び出し直前イベントを流す
for turn in range(1, 5):
    event = BeforeModelCallEvent(
        agent=None,
        invocation_state={},
        projected_input_tokens=4_000,
    )
    registry.invoke_callbacks(event)
    if event.cancel:
        print(f"ターン {turn}: 中断。モデルに渡る理由 ->")
        print(f"  {event.cancel}")
        break
    print(f"ターン {turn}: 通過（積算 {4_000 * turn:,} / 上限 10,000）")
