# 第19章 構造化出力

この章を終えると、モデルの判定をテキストのパースではなく、検証済みの Pydantic インスタンスとして受け取れるようになります。
先にパース版を壊して故障モードを実物で見てから、それが消える書き方に置き換えます。

この章も独立した uv プロジェクトです。最初に依存を入れてください。

```bash
cd 19-structured-output
uv sync
```

## 19.1 概要

### 19.1.1 構造化出力とは

構造化出力は、モデルの応答を自由なテキストではなく、あらかじめ定義したスキーマに沿ったデータとして受け取る仕組みです。
Strands では Pydantic モデルをスキーマとして渡し、検証済みのインスタンスを直接受け取れます。
「形式を守ってほしい」とプロンプトで頼む代わりに、形式そのものを API の契約にします。

### 19.1.2 テキストパースという故障モード

この章の題材は、報告文を検証して approve / revise を判定するレビュー処理です。
素朴に作ると、システムプロンプトで「1 行目は必ず `VERDICT: approve` か `VERDICT: revise`」と指示し、返ってきたテキストをパースする形になります。
動いてはいても、これはお願いベースの構造化です。

モデルが形式を守らない可能性は常に残ります。
前置きを書いてから判定を出す、`判定: approve` と言い換える、そもそも書き忘れる。
パーサ側は読めなければ revise と扱うことで安全側に寄せられますが、本来 approve の報告が revise 扱いになれば、無駄な修正パスが 1 回走ります。
故障モードであると同時に、コストの問題でもあります。

## 19.2 実装のポイント

### 19.2.1 スキーマの渡し方

Strands では、呼び出し時に `structured_output_model` へ Pydantic モデルを渡すと、結果が `result.structured_output` に検証済みのインスタンスとして入ります（章の venv にある strands-agents 1.53.0 のソースで確認済み。`Agent.structured_output()` メソッドもありますが deprecated です）。

```python
result = agent(prompt, structured_output_model=Verdict)
verdict = result.structured_output  # Verdict インスタンス。得られなければ None
```

パース版と比べたときの差は 3 つあります。

- 型と選択肢（`Literal["approve", "revise"]`）はスキーマで強制される。言い換えは起きない
- フィールドの description がモデルへの指示を兼ねる。プロンプトの形式指定が要らなくなる
- パーサが消える。パース失敗という故障モードごと消える

第3章の「docstring は仕様書」と同じ原理です。
自然文で交わしていた約束を、機械が検証できるスキーマに置き換えます。

### 19.2.2 失敗の倒し方

構造化出力でも、判定を取得できないケースは残ります。
呼び出しが例外を投げるか、`structured_output` が `None` のまま返ってくるかのどちらかです。
このとき revise に倒します。判定不能を「問題なし」に倒したら、検証機構として意味をなさないからです。

### 19.2.3 使いどころの整理

構造化出力が向くのは、後段がプログラムである出力です。
判定・分類・抽出のように、結果をコードが分岐やデータとして使う場面がこれにあたります。
逆に人間が読む報告文は自由なテキストのままが適切で、「この出力の消費者は誰か」で使い分けます。

## 19.3 【ハンズオン】structured_verdict を実装する

パース版と構造化出力版を並べて持つミニレビュー処理を作ります。
編集するのは `exercises/review.py` の 1 ファイルだけです。

### 19.3.1 パーサの故障モードを見る

まず提供済みのパース版 `parse_verdict_text` を壊します。
書き手は全部 approve のつもりで、形式だけが違う 4 つの入力を流すスクリプトを用意してあります（編集不要）。

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
パーサの実装を直しても、モデルが形式を破る余地そのものは残ります。次の節でパーサごと消します。

### 19.3.2 TODO を 2 つ埋める

`exercises/review.py` を開いてください。
`Verdict` モデルと `parse_verdict_text` は提供済みで、`structured_verdict` に TODO が 2 つ残っています。

1. `structured_output_model=Verdict` 付きで agent を呼び、`result.structured_output` を返す
2. 例外と `None` を revise の Verdict に倒す（19.2.2 の方針そのまま）

先に判定テスト `verify/test_review.py` を読むのも近道です。
structured_output をスタブ化したダミーエージェントで検証していて、モデルを呼ばずに hooks やエージェントの周辺コードをテストする第6章の技法の応用です。

### 19.3.3 合格判定

実装できたら TODO コメントを消して判定を流します。

```bash
uv run pytest -q
```

`7 passed` で合格です。
Verdict の形・パース版が壊れた入力で誤判定すること・structured_verdict がスキーマと report を渡していること・例外と None が revise に倒れることを検査します。

<details>
<summary>解答例</summary>

```python
def structured_verdict(agent, report: str) -> Verdict:
    prompt = f"# 検証対象の報告\n{report}\n\n上記の報告を検証してください。"
    fallback = Verdict(verdict="revise", reasons=["検証結果を取得できなかったため要修正扱い"])
    try:
        result = agent(prompt, structured_output_model=Verdict)
    except Exception:
        # 判定不能を「問題なし」にしたら検証機構として意味をなさない。revise に倒す
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

自作した `structured_verdict` を実エージェントで呼びます。Bedrock を呼びます。

```bash
uv run 02_structured_call.py
```

出典が無いまま断定している報告を渡すので、`verdict: revise` と reasons の箇条書きが表示されるはずです。
システムプロンプトには検証観点しか書いていません。判定の型と選択肢はスキーマが強制しています。

## 19.4 まとめ

お願いベースの構造化は、モデルが形式を破るたびに安全側の誤判定と無駄な修正パスを生みます。
`structured_output_model` でスキーマを契約にすると、パーサとともにその故障モードが消えます。
残るのは取得できなかったケースだけで、それは revise に倒す 1 つの分岐に収まります。
使いどころは「後段がプログラムである出力」。人間が読む報告文まで構造化する必要はありません。

## 次の章

99-appendix（RAG / Memory / Observability / Gateway の入口）へ。
ここまでで全カリキュラムの実装章は完了です。
