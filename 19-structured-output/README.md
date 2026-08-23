# 第19章 構造化出力

この章を終えると、テキストのパースに頼っていた箇所を構造化出力
（Pydantic モデルへの直接マッピング）に置き換えられるようになります。
題材は ReviewAgent の `VERDICT:` パースの撤去です。

## 19.1 概要

### 19.1.1 構造化出力とは

構造化出力は、モデルの応答を自由なテキストではなく、あらかじめ定義した
スキーマに沿ったデータとして受け取る仕組みです。Strands では Pydantic モデルを
スキーマとして渡し、検証済みのインスタンスを直接受け取れます。
「形式を守ってほしい」とプロンプトで頼む代わりに、形式そのものを API の契約にします。

### 19.1.2 テキストパースという故障モード

現在の ReviewAgent は、システムプロンプトで「1 行目は必ず `VERDICT: ok` か
`VERDICT: revise`」と指示し、返ってきたテキストを `_parse_verdict()` で
パースしています（第5章）。動いてはいますが、これは**お願いベースの構造化**です。

モデルが形式を守らない可能性は常に残ります。前置きを書いてから VERDICT を
出す、`判定: ok` と言い換える、そもそも書き忘れる。パーサ側は「読めなければ
revise と扱う」ことで安全側に寄せてはいるものの、本来 ok の報告が revise 扱いに
なれば無駄な修正パスが 1 回走ります。つまりコストの問題でもあります。

## 19.2 実装のポイント

### 19.2.1 構造化出力の仕組み

Strands の `Agent` は `structured_output_model` に Pydantic モデルを渡せます。
すると応答スキーマがモデル（LLM）に強制され、結果は
`result.structured_output` に**検証済みの Pydantic インスタンス**として入ります
（`AgentResult` のフィールドとして確認済み）。

- 型と選択肢（`Literal["ok", "revise"]`）はスキーマで強制される。言い換えは起きない
- フィールドの description がモデルへの指示を兼ねる。プロンプトの形式指定は不要になる
- パーサが消える = パース失敗という故障モードごと消える

第3章の「docstring は仕様書」と同じ原理です。自然文で交わしていた約束を、
機械が検証できるスキーマに置き換えます。

### 19.2.2 使いどころの整理

構造化出力が向くのは、**後段がプログラムである**出力です。判定・分類・抽出のように、
結果をコードが分岐やデータとして使う場面。逆に人間が読む報告文（Orchestrator の
成果物）は自由なテキストのままが適切です。すべてを構造化するのではなく、
「この出力の消費者は誰か」で使い分けます。

## 19.3 【ハンズオン】ReviewAgent を書き換える

`07-full-app/src/agents/review_agent.py` を次の要件で書き換えてください。

1. Pydantic モデル `ReviewVerdict` を定義する
   - `verdict: Literal["ok", "revise"]` — Field の description に判定基準を書く
   - `notes: str` — 指摘の箇条書き（無ければ「指摘なし」）
2. `Agent(...)` に `structured_output_model=ReviewVerdict` を渡す
3. システムプロンプトから `VERDICT:` の形式指定を削る
   （検証観点 1〜3 は残す。形式はスキーマの仕事、観点はプロンプトの仕事）
4. 構造化結果から `ReviewOutcome` への変換を、テスト可能な純粋関数
   `_outcome_from(verdict: ReviewVerdict | None) -> ReviewOutcome` として切り出す
   - `None`（構造化出力が得られなかった場合）は **revise として扱う**。
     判定不能を「問題なし」にしない方針は従来と同じ
5. `_parse_verdict()` を削除する
6. `07-full-app/tests/test_agents.py` の `_parse_verdict` のテストを、
   `_outcome_from` のテスト（ok / revise / None の 3 パス）に置き換える

判定を流します。

```bash
uv run --project 07-full-app pytest 19-structured-output/verify -q
```

```bash
cd 07-full-app && uv run pytest -q
```

両方通れば合格です。詰まったら `solutions/review_agent.py` を見てください。

## 19.4 挙動を確認する

第13章の eval を流し、退行が無いことを確認してください。

```bash
uv run --project 07-full-app python 13-evaluation/run_eval.py
```

ついでに `token_usage` ログの review ロールを前後比較すると、形式指定の
プロンプトが消えた分と、誤判定による無駄な修正パスが減った分の差が見えることがあります。

## 19.5 まとめ

お願いベースの構造化は、モデルが形式を破るたびに安全側の誤判定と無駄な修正パスを
生みます。**自然文の約束を機械が検証できるスキーマに置き換える**と、パーサとともにその故障モードが
消える——第3章の「docstring は仕様書」から続く原理の到達点です。書き換えたら
第13章の eval で退行が無いことを確認してから先へ進んでください。

## 次の章

99-appendix（RAG / Memory / Observability / Gateway の入口）へ。
ここまでで全カリキュラムの実装章は完了です。
