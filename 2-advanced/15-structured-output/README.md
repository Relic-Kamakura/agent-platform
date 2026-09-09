# 第15章 構造化出力

この章を終えると、モデルの判定をテキストのパースではなく、検証済みの Pydantic インスタンスとして受け取れるようになります。
先にパース版が誤判定する様子を見てから、その誤判定が起きない書き方に置き換えます。

この章は独立した uv プロジェクトです。最初に依存を入れてください。

```bash
cd 2-advanced/15-structured-output
uv sync
```

## 15.1 概要

### 15.1.1 構造化出力とは

構造化出力は、モデルの応答を自由なテキストではなく、あらかじめ定義したスキーマに沿ったデータとして受け取る仕組みです。
Strands では Pydantic（型注釈でデータの形を定義し、検証まで行う Python ライブラリ）のモデルをスキーマとして渡すと、検証済みのインスタンスが返ります。
形式をプロンプトで指示する代わりに、API の引数として渡します。

### 15.1.2 テキストをパースする方式の問題

この章の題材は、報告文を検証して approve / revise を判定するレビュー処理です。
素朴に作ると、「1 行目は必ず `VERDICT: approve` か `VERDICT: revise`」とシステムプロンプトで指示し、返ってきたテキストをパースする形になります。
形式が守られるかはモデル次第で、前置きを書いてから判定を出す、`判定: approve` と言い換える、判定行を書き忘れる、のどれも起こりえます。

パーサは読み取れなかった応答を revise 扱いにしておけば、誤って承認することはありません。
ただし本来 approve の報告が revise になると、報告の修正が 1 回余計に実行されます。
誤判定であると同時に、コストの問題でもあります。

## 15.2 実装のポイント

### 15.2.1 スキーマの渡し方

呼び出し時に `structured_output_model` へ Pydantic モデルを渡すと、結果が `result.structured_output` に検証済みのインスタンスとして入ります。

```python
result = agent(prompt, structured_output_model=Verdict)
verdict = result.structured_output  # Verdict インスタンス
```

Strands は渡された Pydantic モデルをツールのスキーマへ変換し、モデルにそのツールを呼ばせて引数を検証します（章の `.venv` の `strands/tools/structured_output/`）。
値の選択肢（`Literal["approve", "revise"]`）はスキーマが強制するため、言い換えは起きません。
フィールドの description がモデルへの指示を兼ね、プロンプトに形式の指定を書く必要もなくなります。

### 15.2.2 判定を取得できなかったとき

判定を取得できない場合、その多くは例外になります。
`max_tokens` に達して生成が止まったときは `MaxTokensReachedException`、モデルが構造化出力のツールを呼ばずに応答を終えたときは、Strands が強制モードでもう一度要求したうえで、それでも呼ばなければ `StructuredOutputException` を送出します（`strands/event_loop/event_loop.py`）。

呼び出しは try/except で囲み、例外を捕まえたら revise 扱いにします。
判定不能を approve として扱うと、検証の仕組みとして意味をなさないからです。
`MaxTokensReachedException` が続くときは、`max_tokens` の値とスキーマのフィールド数を見直します。
`result.structured_output` が `None` のまま返る経路も残っているので、解答例ではその分岐も残しています。

### 15.2.3 どの出力を構造化するか

構造化出力が向くのは、判定や分類のように、結果をコードが分岐やデータとして使う出力です。
人間が読む報告文は自由なテキストのままにします。

## 15.3 ハンズオン: パーサの誤判定を観察する

提供済みのパース版 `parse_verdict_text` に、内容はどれも approve で形式だけが違う 4 つの入力を渡します。
実行スクリプトは用意してあります（編集不要）。

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
パーサの実装を直しても、モデルが形式を守らない可能性は残ります。

## 15.4 ハンズオン: 構造化出力を実装する

パース版と構造化出力版を並べて持つミニレビュー処理を作ります。
編集するのは `exercises/review.py` の 1 ファイルだけです。

### 15.4.1 TODO を 2 つ埋める

`exercises/review.py` を開いてください。
`Verdict` モデルと `parse_verdict_text` は提供済みで、`structured_verdict` に TODO が 2 つ残っています。

1. `structured_output_model=Verdict` 付きで agent を呼び、`result.structured_output` を返す
2. 例外のときと `None` のときは revise の Verdict を返す（15.2.2 の方針そのまま）

判定テスト `verify/test_review.py` は、`structured_output` を固定値に差し替えたダミーエージェントを渡して検証します。
モデルを呼ばないので、実装の途中でも繰り返し実行できます。

### 15.4.2 実行する

自作した `structured_verdict` を、Bedrock を呼ぶエージェントで動かします（このスクリプトは編集しません）。

```bash
uv run 02_structured_call.py
```

出典が無いまま断定している報告を渡すので、`verdict: revise` と reasons の箇条書きが表示されるはずです。
システムプロンプトには検証観点しか書いていません。判定の値の型と選択肢はスキーマが強制しています。

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

### 15.4.3 合格判定

TODO コメントを消し、判定を実行します。

```bash
uv run pytest -q
```

`7 passed` で合格です。
Verdict の定義、パース版が形式違いの入力で誤判定すること、`structured_verdict` がスキーマと report を渡していること、例外と `None` のときに revise の Verdict になることを検査します。

## 15.5 まとめ

プロンプトで形式を指示する方式は、モデルが形式を守らないたびに安全側の誤判定と余計な再実行を生みます。
`structured_output_model` にスキーマを渡すと、パーサが不要になり、その誤判定も起きなくなります。
残るのは判定を取得できなかった場合で、Strands はそれを例外として送出します。
呼び出しを try/except で囲み、revise 扱いにしておきます。

## 次の章

[第16章 更新情報ナレッジベースと MCP 読み取り経路](../16-news-kb-mcp/)
