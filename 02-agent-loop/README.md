# 第2章 はじめてのエージェント

この章を終えると、ツール付きのエージェントを自分の手で書き、実行ログの各行が
ReAct のどのステップかを言い当てられるようになります。

この章も独立した uv プロジェクトです。

```bash
cd 02-agent-loop
uv sync
```

## 2.1 概要

### 2.1.1 エージェント = ループする LLM 呼び出し

第1章の `01_converse.py` は 1 回呼んで終わりでした。エージェントとの違いは
ループの有無だけです。

1. モデルに質問と「使えるツールの一覧」を渡す
2. 応答がテキストだけなら、それが最終回答。終了
3. 応答が「ツール X を引数 Y で使いたい」なら、X を実行し、結果を履歴に足して 1 へ戻る

内部では Converse API のマルチターンが動いています。ツール要求は `toolUse` ブロック
（`toolUseId` 付き）で返り、呼び出し側は実行結果を `toolResult` ブロックとして次の
リクエストに追加します。ツールを実行するのはモデルではなく、モデルを呼び出している
側のコード、つまりこの章で自分が書く Python コードです。

### 2.1.2 ReAct と CoT

このループには名前が付いています。ReAct は Yao らの論文（2022、ICLR 2023 採録）で
提案されたパターンで、推論だけで完結させず外部と相互作用しながら考える方が
幻覚が減るというのが主張でした。2.3 で自分のループを書いたあと、2.4 で
1 行ずつ対応を確かめます。

CoT（Chain of Thought、Wei らの論文 2022）は、複雑な問題を思考ステップに
分解させるプロンプト技法です。ループの構造ではなくプロンプトの書き方であり、
フレームワークの機能ではありません。

本体での実物は `07-full-app/src/agents/orchestrator.py` のシステムプロンプトの一文、
「依頼を 2〜4 個の調査観点に分解し、観点ごとに investigate を 1 回ずつ呼ぶ」。
この指示が無いと、モデルは依頼内容全体を 1 回の検索クエリに詰め込み、浅い調査で結論を出しがちです。
この分解をどこまでモデルの裁量に任せ、どこからコードで固定するかという設計判断は、
第5章の主題です。

## 2.2 実装のポイント

Strands の `Agent` はこの往復の実装で、1 往復を cycle と呼びます。何周したかは
`result.metrics.cycle_count`、消費トークンの累計は `result.metrics.accumulated_usage`
で取れます。第4章では、この 2 つの数字を使ってループ回数とトークン消費に
上限を掛けます。

もうひとつ、`tools` に渡した関数の docstring はそのままモデルに渡ります。
モデルはその文面だけで「いつ使うか」を決めるので、docstring の質がツール選択の質を
決めます。書き方の規約は第3章で扱い、この章のハンズオンでは 3 節構成
（受け取るもの / 返すもの / 含まないもの）を先取りします。

## 2.3 【ハンズオン】最小のエージェントを書く

`01_agent.py` を作成し、次のコードを自分の手で書いてください。

```python
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
```

実行します。

```bash
uv run 01_agent.py
```

回答のあとに `cycles: 2` が出るはずです。1 周目でモデルが「now を使う」と判断し、
2 周目でツール結果を見て回答を組み立てた、という意味です。

## 2.4 いま書いたものを ReAct として読む

2.3 で書いたループが、ReAct の 3 ステップにそのまま対応します。

| ReAct のステップ | 2.3 のコードでの実体 |
| --- | --- |
| Reasoning（推論） | 1 周目の応答テキスト「日時を知る必要がある」 |
| Acting（行動） | `toolUse` ブロック → now() の実行 |
| Observation（観察） | `toolResult` が 2 周目の入力に入る |

実際のログで見るとこうなります。本体 07-full-app を 1 回呼んだときの抜粋です。

```
[ops]         {"message": "startup", "orchestrator": "apac.anthropic..."}   ← ループ外の運用ログ
[Reasoning]   モデル応答: "依頼を『Acme の価格』『Globex の価格』の 2 観点に分解します"
[Acting]      {"message": "web_search", "query": "Acme pricing", "hits": 2}
[Observation] 次ターンの入力に tool_result として検索結果 2 件が追加された
[Reasoning]   モデル応答: "Acme は得られた。次に Globex を調べる必要がある"
[ops]         {"message": "token_usage", "total_tokens": 8412, "cycle_count": 4}
```

案件で「ReAct で作っていますか」と聞かれたら、「Strands のイベントループがそれです。
ターン数は hooks で制御しています（第4章）」で答えられます。

## 2.5 【ハンズオン】ツールを自分で追加する

写経ではなく、今度は自分で設計します。`02_add_tool.py` を作成してください。
`01_agent.py` の内容をベースに、ツールをもう 1 つ増やします。

要件:

1. `char_count(text: str) -> str` — 受け取った文字列の文字数を返すツールを追加する
2. docstring は第3章で学ぶ規約の先取りで、**受け取るもの / 返すもの / 含まないもの**の
   3 節を必ず書く（「含まないもの」には単語数のカウントはしない、など否定を 1 つ以上）
3. `Agent` の `tools` に `now` と `char_count` の両方を渡す
4. `__main__` では「『こんにちは世界』は何文字？」と質問する

実行します。

```bash
uv run 02_add_tool.py
```

「7 文字」という趣旨の回答と `cycles: 2` が出るはずです。
docstring を雑にする（1 行だけにする）とツールが選ばれにくくなることも、
時間があれば試してください。ツール選択の根拠が docstring だと体感できます。

## 2.6 【ハンズオン】メトリクスを観察する

`03_metrics.py` を作成し、次を書いてください。

```python
"""同じエージェントで、ツールが要る質問と要らない質問のコスト差を見る。"""

from importlib import import_module

mod = import_module("02_add_tool")
agent = mod.agent

for question in ("こんにちは", "今日は何日？『こんにちは世界』は何文字？"):
    result = agent(question)
    usage = result.metrics.accumulated_usage
    print(f"\nQ: {question}")
    print(f"  cycles={result.metrics.cycle_count}  tokens={usage.get('totalTokens')}")
```

実行します。

```bash
uv run 03_metrics.py
```

1 問目は cycles=1、2 問目はツールを 2 回使うので cycles=3 前後になり、
トークン数も数倍になるはずです。ツールを 1 回使うたびに履歴が膨らみ、
モデル呼び出しが 1 回増える。この構造が第4章のコスト制御につながります。

## 2.7 合格判定

```bash
uv run pytest -q
```

`6 passed` で合格です（エージェントの構造だけを検査します）。

## 2.8 まとめ

エージェントと呼ばれているものの実体は、**ツール結果を履歴に積みながら繰り返す
Converse 呼び出し**です。1 周増えるたびにモデル呼び出しと履歴が増え、トークン消費が
積み上がる — 2.6 で観察したこの構造が、第4章で上限を掛ける理由になります。
次はループの質を決めるツールの側に踏み込みます。

## 次の章

[第3章 ツール設計](../03-tool-design/)
