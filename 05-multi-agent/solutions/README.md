# 演習 05 模範解答

## 1. 新規ファイル

[pricing_agent.py](pricing_agent.py) を `07-full-app/src/agents/pricing_agent.py` として配置する。

## 2. `07-full-app/src/agents/orchestrator.py` の変更（2 箇所）

import と tools への追加:

```python
from .pricing_agent import build_pricing_agent_tool
...
            tools=[build_search_agent_tool(settings), build_pricing_agent_tool(settings)],
```

システムプロンプトの「守ること」に 1 文追加:

```
- 価格の比較が求められたときは investigate ではなく compare_pricing を使う。
```

## 設計のポイント

- **モデルは search ロール（軽量）**。表への整形は定型処理であり、上位モデルを使うのはコストの無駄。
  「どの競合を比較すべきか」という判断は Orchestrator 側に残っている
- **compare_pricing と investigate の棲み分けを docstring で明示**。
  これが無いと Orchestrator はどちらを使うべきか毎回迷う（= 挙動が不安定になる）
- **専門エージェントにもガードを付ける**。ガードなしのエージェントを 1 体でも作ると、
  そこが暴走の穴になる
