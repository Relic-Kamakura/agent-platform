---
name: review-and-commit
description: 教材（章の README と exercises、solutions、verify、本体コード、docs）を修正するときの標準手順。着手前の宣言、構成と技術の確認、章内完結と分量の規約、機械検証（verify のラウンドトリップ、リンク、Mermaid、文体）、docs/plan.md への記録、1 文コミットまでを 1 本にまとめる。教材の修正・改訂・レビュー・コミットはすべてこの手順で行う。
metadata:
  trigger: 章の修正、README の改訂、exercises / solutions / verify の変更、本体 07-full-app の変更、docs の更新、レビュー、コミット
  language: ja
---

# review-and-commit

教材を直すときの手順。読んでから直し、直したら測り、測ったら記録して、章ごとにコミットする。
この手順を経ずに教材ファイルを編集すると、`.claude/hooks/require-review-skill.sh` が編集を止める。

## 0. 着手の宣言

最初に 1 回だけ実行する。編集を許可するマーカーを置く（12 時間有効。`.gitignore` 済み）。

```bash
.claude/skills/review-and-commit/scripts/start.sh
```

同時に `docs/writing-style.md` と `.claude/skills/stop-ai-slop-jp/SKILL.md`、`references/textbook.md` を読む。

## 1. 守ること

- **AWS を呼ばない。** `aws` CLI、Bedrock、KB、Gateway、`cdk deploy`、Docker のビルドと実行は実行しない。実機確認はユーザーが行う。`uv run pytest`、`uv run python` によるライブラリの内省、`npx tsc --noEmit`、`npx cdk synth` は使ってよい
- **教材外の資料に言及しない。** 参考にした社外の資料、他案件、顧客名、フォルダパスを、教材本文、コメント、docs、スキルのどこにも書かない。「ある案件で〜」形式の経験談も書かない。根拠は「AWS / Strands / boto3 の仕様としてこう動く。そのため〜する」の形で書き、公式ドキュメントかライブラリのソースで裏取りできたものだけ書く
- **章内完結。** 他章を先に終えている前提や「第N章で学ぶ」「第N章参照」を書かない。他章への参照は文末の `## 次の章` リンクだけ。必要な説明はその場で 1〜2 文書く。各章の冒頭にその章のセットアップ（`cd` と `uv sync` / `npm ci`）を置く
- **分量。** `N.1 概要` + `N.2 実装のポイント` でコードブロックを除き日本語 1,200 字以内、README 200 行以内、新出概念 1 章 5 個まで。TODO を埋めるのに要らず、実行時に学習者が踏まない話は書かない
- **ハンズオンの型。** `### N.x.1 TODO を n 個埋める`（骨組みの cp を先頭に）→ `### N.x.2 実行する`（期待結果を明記し、直後に `<details><summary>解答例</summary>`）→ `### N.x.3 合格判定`
- **記述式の設問を置かない。** 「自分の言葉で答えてください」「考えてみてください」のような機械判定の無い節は作らない。到達点は「〜が動く」「〜を書いて synth で確認できる」のように手を動かした結果で書く
- **初見で意味が取れない語を使わない。** 「契約」「型」「生 HTML」のような省略や比喩は、その文が指すものを具体語で書く（置換表は `stop-ai-slop-jp/references/textbook.md`）
- **上限ガードを外さない。リージョン・ロール ARN・モデル ID を直書きしない。** CLAUDE.md の規約どおり

## 2. 確認（直す前に読む）

対象の章について、次を確かめてから編集に入る。

1. 構成: 概要 → 実装のポイント → ハンズオン → まとめ → 次の章の並びか。概要が TODO を埋める材料（コード断片、API 名）を出しているか。期待結果と合格判定があるか
2. 密度: 分量を測る。超過していれば、削る節を先に決める

```bash
.claude/skills/review-and-commit/scripts/measure_chapters.py
```

3. 技術: README とコードの主張を、章 venv のライブラリソース（`uv run python -c "import inspect; ..."`）と公式ドキュメント（WebFetch）で照合する。API 名、引数名、既定値、例外の種類、CloudFormation のプロパティ名を確認する。裏取りできない仕様は書かない
4. 章内完結と禁止表現を機械で拾う

```bash
.claude/skills/review-and-commit/scripts/check_text.sh
```

## 3. 修正

- README の節番号を変えたら、verify の失敗メッセージと exercises の TODO コメントの節参照を追従させる
- 解答例の `<details>` は「実行する」節の末尾に置く。期待出力は solutions を適用した状態で実際に実行した結果を貼る（AWS を呼ぶ工程は除く）
- `.py` を変えたら Pyright で import の解決を確認する（`uvx pyright --pythonpath <章>/.venv/bin/python <変更ファイル>`）。骨組みの `...` と verify が渡す `None` の型エラーは既知で対象外
- 本体 `1-basic/07-full-app` を変えたら `uv run ruff check src tests` / `uv run mypy src` / `uv run pytest -q` を通す

## 4. 検証

すべて素の状態（exercises に TODO が残る状態）で行い、リポジトリ内の exercises は素のまま残す。

```bash
.claude/skills/review-and-commit/scripts/verify_roundtrip.sh <章ディレクトリ>
```

素 = 案内付きで fail、solutions 適用（scratchpad へのコピー上で）= 全パス、の両方を確認する。09（ルートから `uv run --project 1-basic/07-full-app pytest 2-advanced/09-evaluation/verify -q`）、13 / 16（`mkdir -p lib && cp exercises/*.ts lib/` のあと `./verify/verify.sh`）、17（Docker ビルドを伴うため案内文の整合だけ）、18〜20（`./verify/verify.sh`）は README の手順に従う。

```bash
.claude/skills/review-and-commit/scripts/check_links.py
.claude/skills/review-and-commit/scripts/check_mermaid.sh
```

リンク切れ 0 件、Mermaid の解析 NG 0 件になること。Mermaid は古いレンダラでも通る形（連結矢印を 1 行 1 辺に、ラベルは二重引用符、`participant ... as` に `<br/>` と括弧を入れない）で書く。

## 5. 文体レビュー

変更した README と Python の docstring / TODO コメントを `stop-ai-slop-jp` の基準で 1 回レビューして直す。比喩と擬人化、命題型の見出し、全角ダッシュ、中黒による 3 項目並列、予告と総括、「〜が分かります」、敬体と常体の混在、文の途中での改行を対象にする。

## 6. 記録

`docs/plan.md` の先頭（ステータス行の直後）に、日付付きの見出しで「何を、なぜ直したか」「削った節と理由」「検証結果」「裏取りできず書かなかったこと」を書く。最終更新日も更新する。

## 7. コミット

章ごと、または関心ごとに 1 コミット。

- メッセージは日本語 1 文の短文（例: 「第13章の Guardrail に Standard tier と cross-Region 設定を追加する」）
- 作成者の注記（Co-Authored-By など AI の記載）は書かない
- push はしない。ユーザーが行う
- コミット前に `git status` で対象を確認し、生成物（`.venv/` `node_modules/` `cdk.out/` `__pycache__/`）を含めない

## 出力

作業の最後に、章ごとの「変更点 / 削った節と理由 / 検証結果 / 直せなかった点・裏取りできず書かなかった点」を短く報告する。
