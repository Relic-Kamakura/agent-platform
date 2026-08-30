# 第19章 構造化出力

この章を終えると、モデルの判定をテキストのパースではなく、検証済みの Pydantic インスタンスとして受け取れるようになります。
先にパース版が誤判定する様子を見てから、その誤判定が起きない書き方に置き換えます。

この章も独立した uv プロジェクトです。最初に依存を入れてください。

```bash
cd 19-structured-output
uv sync
```

## 19.1 概要

### 19.1.1 構造化出力とは

構造化出力は、モデルの応答を自由なテキストではなく、あらかじめ定義したスキーマに沿ったデータとして受け取る仕組みです。
Strands では Pydantic（型注釈でデータの形を定義し、検証まで行う Python ライブラリ）の
モデルをスキーマとして渡し、検証済みのインスタンスを直接受け取れます。
プロンプトで形式を指示する代わりに、形式を API の引数として渡します。

### 19.1.2 テキストをパースする方式の問題

この章の題材は、報告文を検証して approve / revise を判定するレビュー処理です。
素朴に作ると、システムプロンプトで「1 行目は必ず `VERDICT: approve` か `VERDICT: revise`」と指示し、返ってきたテキストをパースする形になります。
動いてはいても、形式が守られるかはモデル次第です。

モデルが形式を守らない可能性は常に残ります。
前置きを書いてから判定を出す、`判定: approve` と言い換える、書き忘れる、のいずれも起こりえます。
パーサ側は読めなければ revise として扱えば安全側になりますが、本来 approve の報告が revise 扱いになれば、報告の修正が 1 回余計に実行されます。
誤判定であると同時に、コストの問題でもあります。

## 19.2 実装のポイント

### 19.2.1 スキーマの渡し方

Strands では、呼び出し時に `structured_output_model` へ Pydantic モデルを渡すと、結果が `result.structured_output` に検証済みのインスタンスとして入ります（章の venv にある strands-agents のソースで確認。バージョンは versions.md。`Agent.structured_output()` メソッドもありますが非推奨です）。

```python
result = agent(prompt, structured_output_model=Verdict)
verdict = result.structured_output  # Verdict インスタンス。得られなければ None
```

パース版と比べたときの差は 3 つあります。

- 値の型と選択肢（`Literal["approve", "revise"]`）はスキーマで強制され、言い換えは起きない
- フィールドの description がモデルへの指示を兼ね、プロンプトの形式指定が要らなくなる
- パーサが不要になり、パースの失敗そのものが起きなくなる

第3章の「docstring は仕様書」と同じ原理です。
自然文で指示していた形式を、機械が検証できるスキーマに置き換えます。

### 19.2.2 判定を取得できなかったとき

構造化出力でも、判定を取得できないケースは残ります。
呼び出しが例外を投げるか、`structured_output` が `None` のまま返ってくるかのどちらかです。
このときは revise 扱いにします。判定できなかったものを approve として扱うと、検証の仕組みとして意味をなさないからです。

`None` になる原因で多いのが、出力の途中切れです。
`max_tokens` に達すると生成はそこで止まり、例外にはなりません（第1章 1.1.4）。
JSON が閉じないまま返るので、スキーマ検証に失敗して `None` になります。
スキーマを厳しくしてもこの失敗は防げません。
出力の長さの問題だからです。

切れたかどうかは `stopReason` で分かります。
`max_tokens` で終わっているのに `structured_output` が `None` なら、プロンプトではなく `max_tokens` の値を疑うところです。
判定のような短い構造化出力は、フィールドを増やしすぎないことでも避けられます。

### 19.2.3 どの出力を構造化するか

構造化出力が向くのは、後段がプログラムである出力です。
判定、分類、抽出のように、結果をコードが分岐やデータとして使う場面がこれにあたります。
逆に人間が読む報告文は自由なテキストのままにし、出力を受け取るのがプログラムか人かで使い分けます。

## 19.3 【ハンズオン】structured_verdict を実装する

パース版と構造化出力版を並べて持つミニレビュー処理を作ります。
編集するのは `exercises/review.py` の 1 ファイルだけです。

### 19.3.1 パーサが誤判定する様子を見る

まず、提供済みのパース版 `parse_verdict_text` に 4 つの入力を渡します。
4 つとも内容は approve ですが、形式だけが違います。実行スクリプトは用意してあります（編集不要）。

```bash
uv run 01_break_parser.py
```

こう表示されるはずです。

```
約束どおりの応答       | 1 行目: VERDICT: approve
                       | パース結果: approve

前置きを書いてから判定 | 1 行目: 報告を確認しました。結論は以下です。
                       | パース結果: revise

判定行を言い換えた     | 1 行目: 判定: approve
                       | パース結果: revise

判定行を書き忘れた     | 1 行目: 指摘なし。よくまとまった報告です。
                       | パース結果: revise
```

4 つのうち 3 つが誤判定です。
パーサの実装を直しても、モデルが形式を守らない可能性は残ります。次の節ではパーサ自体を無くします。

### 19.3.2 TODO を 2 つ埋める

`exercises/review.py` を開いてください。
`Verdict` モデルと `parse_verdict_text` は提供済みで、`structured_verdict` に TODO が 2 つ残っています。

1. `structured_output_model=Verdict` 付きで agent を呼び、`result.structured_output` を返す
2. 例外と `None` のときは revise の Verdict を返す（19.2.2 の方針そのまま）

先に判定テスト `verify/test_review.py` を読むと分かりやすくなります。
`structured_output` を固定値に差し替えたダミーエージェントで検証しており、モデルを呼ばずにエージェントの周辺コードをテストする第6章の技法の応用です。

### 19.3.3 合格判定

実装できたら TODO コメントを消して判定を実行します。

```bash
uv run pytest -q
```

`7 passed` で合格です。
Verdict の定義、パース版が形式違いの入力で誤判定すること、structured_verdict がスキーマと report を渡していること、例外と None のときに revise の Verdict になることを検査します。

<details>
<summary>解答例</summary>

```python
def structured_verdict(agent, report: str) -> Verdict:
    prompt = f"# 検証対象の報告\n{report}\n\n上記の報告を検証してください。"
    fallback = Verdict(verdict="revise", reasons=["検証結果を取得できなかったため要修正扱い"])
    try:
        result = agent(prompt, structured_output_model=Verdict)
    except Exception:
        # 判定不能を「問題なし」にしたら検証の仕組みとして意味をなさない。revise 扱いにする
        logger.warning("structured_output_failed report_chars=%s", len(report), exc_info=True)
        return fallback
    if result.structured_output is None:
        logger.warning("structured_output_missing report_chars=%s", len(report))
        return fallback
    return result.structured_output
```

全文は `solutions/review.py` にあります。

</details>

### 19.3.4 実モデルで判定させる（任意）

自作した `structured_verdict` を、Bedrock を呼ぶ実際のエージェントで動かします。

```bash
uv run 02_structured_call.py
```

出典が無いまま断定している報告を渡すので、`verdict: revise` と reasons の箇条書きが表示されるはずです。
システムプロンプトには検証観点しか書いていません。判定の値の型と選択肢はスキーマが強制しています。

## 19.4 まとめ

プロンプトで形式を指示する方式は、モデルが形式を守らないたびに安全側の誤判定と余計な再実行を生みます。
`structured_output_model` にスキーマを渡すと、パーサとともにその誤判定が起きなくなります。
残るのは判定を取得できなかったケースだけで、revise 扱いにする分岐 1 つで済みます。

## 次の章

[付録 発展領域の入口](../99-appendix/)（RAG / Memory / Observability / Gateway）。実装を伴う章はこの第19章までです。
