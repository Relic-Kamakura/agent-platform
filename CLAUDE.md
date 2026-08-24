# CLAUDE.md

エージェント開発の学習リポジトリ。Strands Agents (Python 3.12+/uv) を Amazon Bedrock
AgentCore Runtime にコンテナデプロイし、CDK (TypeScript) と Next.js を組み合わせる。
**ルート直下の番号付きディレクトリが学習の章**であり、`07-full-app` と `09-infra-as-code` は
章であると同時に動くコードの本体。題材は競合リサーチエージェント。

## 詳細ドキュメント

手順・構成・設計思想はここには書かない。以下を参照する。

- 章の一覧と進め方: @README.md
- 実装計画とフェーズ進捗: @docs/plan.md
- 習得項目の優先度と習得判定: @docs/learning-roadmap.md
- 遭遇した事象の記録: @docs/troubleshooting.md

## ディレクトリの要点

- `NN-*/` — 学習の章。各章は README（章番号付き節 + 【ハンズオン】節）+ exercises/（TODO 付き骨組み）+
  verify/（合格判定）+ solutions/。多くの章は独立した uv プロジェクト
- `07-full-app/` — エージェント本体（完成形）。**ハンズオンは各章内で完結させ、
  本体は読み比べの対象にする**（旧方式で本体を改造する章が一部残っており、穴埋め移行時に改める）
  - `src/main.py` エントリポイント（HTTP 契約はここだけ）/ `src/config.py` 環境変数を読む唯一の場所
  - `src/agents/` オーケストレータと専門エージェント / `src/tools/` 1 ファイル 1 ツール
  - `src/errors.py` 例外定義 / `src/guards.py` 上限ガードとトークン計測
- `09-infra-as-code/` — CDK。`lib/config.ts` が context を読む唯一の場所
- `scripts/check_env.sh` — 前提条件チェック。困ったらまずこれ
- 10 以降の章は knowledge-base / auth / frontend / evaluation / security / mcp /
  prompt-caching / guardrails / hitl / structured-output（10〜19）

## コマンド

### 07-full-app/

- 依存解決: `uv sync` / テスト: `uv run pytest`
- Lint・型: `uv run ruff check .` `uv run ruff format .` `uv run mypy src`
- ローカル起動: `uv run python -m src.main`（`:8080`。塞がっていたら `SERVER_PORT=8181`）
- コンテナ: `docker buildx build --platform linux/arm64 -t agent-platform/agent .`

### 09-infra-as-code/

- 依存解決: `npm ci` / 型: `npx tsc --noEmit`
- 差分・デプロイ: `npx cdk diff` / `npx cdk deploy --all`（直接 --all は禁止。deploy.sh を使う）

### 12-streaming/

- 依存解決: `npm ci` / 型: `npm run typecheck` / 開発サーバ: `npm run dev`

### リポジトリルート

- 前提条件チェック: `./scripts/check_env.sh`
- デプロイ一式: `./scripts/deploy.sh`（ECR → イメージ push → Runtime の順序を保証）
- 章の合格判定: 各章ディレクトリで `uv run pytest -q`。例外は
  13 章（`uv run --project 07-full-app pytest 13-evaluation/verify -q`）、
  08・09・11・12 章（`<章>/verify/verify.sh`）、17 章（verify.sh と章内 pytest の両方）

## 必ず守る規約

- **コンテナは ARM64 でビルドする。** AgentCore Runtime は `linux/arm64` のみ受け付ける。
  `docker buildx` に `--platform linux/arm64` を明示する。
- **リージョン・実行ロール ARN・Bedrock モデル ID をハードコードしない。**
  Python は `.env` 経由で `07-full-app/src/config.py` から、CDK は context 経由で
  `09-infra-as-code/lib/config.ts` から読む。テスト・例・章の教材コードも例外にしない。
- **ツール呼び出し上限とターン数上限を外さない。** 上限値は `.env` で変えてよいが、
  ガード自体を無効化・削除しない。ガードなしのエージェントを新設しない。
- **ツールの docstring は「LLM がツールを選択するための仕様書」として書く。**
  受け取るもの / 返すもの / 含まないもの、の 3 節を必ず含める。
- **1 ツール 1 責務。** フラグで挙動を切り替えるツールを作らない。
- **例外を握りつぶさない。** ツール失敗は retryable と次の行動をエージェントに返す。
  例外は `07-full-app/src/errors.py` に定義する。
- **外部 API 呼び出しにはタイムアウトとリトライを入れる。** 値は config から取る。
- **1 リクエストあたりのトークン消費をログに出す。**（`result.metrics` 経由）
- **モデルの役割別割り当てを変更したら理由をコメントに残す。**
- **Phase をまたいで先走らない。** `docs/plan.md` の現在フェーズの範囲だけを実装する。

## 章を追加・変更するときの規約

- 文章は @docs/writing-style.md のガイドに従う（本文中の予告・総括・空虚な修飾・
  箇条書き乱用の禁止、実測値と因果メカニズムで書く）
- 章の節の並びは固定: 冒頭（到達点）→ `## N.1 概要` → `## N.2 実装のポイント` →
  `## N.x 【ハンズオン】...` → `## N.last まとめ` → `## 次の章`。手本は
  `01-invoke-bedrock/README.md`、詳細は writing-style.md の「章の構成」。
  コマンドは 1 ブロック 1 実行単位。演習ファイルは分けず README に統合する
- **ハンズオンは穴埋め方式を標準とする**（現在は第1章のみ適用済み。他章は順次移行）。
  学習者が修正するコードは章直下の `exercises/` に TODO 付きの骨組み（連番 `01_*.py`）
  として置き、完成形を `solutions/` に置く。README は概要節に TODO を埋めるための
  具体構造を書き、ハンズオン節末に開閉式（`<details>`）の解答例を付ける。
  verify は TODO の残存を検出して該当節へ誘導する
- 合格判定は機械実行できる形にする（pytest かスクリプト）。「読んだら終わり」の章を作らない
- verify は solutions を適用した状態で全パスすることを確認してから追加する
- 空のプレースホルダディレクトリを作らない。実体ができる Phase で章を追加する

## やってはいけないこと

- VPC を作らない。AgentCore Runtime のマネージドネットワークを使う。
- 「念のため」の防御的コードを書かない。読みやすさを優先する。
- `docs/troubleshooting.md` に一般的なトラブル集を書かない。実際に遭遇した事象のみ。
- 秘密情報をコミットしない（`.env` / トークン / アカウント ID 直書き）。
- ECR と AgentCore Runtime を同一デプロイで新規作成しない（deploy.sh の順序を守る）。
- 生成物（`.venv/` `node_modules/` `cdk.out/` `__pycache__/`）をコミットしない。

## 進め方

- 変更を入れたら、対応する層のテストと関係する章の verify を実行してから完了とする。
- **README 等の md 文書を作成・変更したら、必ず `stop-ai-slop-jp` スキル
  （`.claude/skills/stop-ai-slop-jp/SKILL.md`）でレビューしてから完了とする。**
  writing-style.md のガイドと併用する（構成は writing-style、文の AI 臭は本スキル）。
- 事実確認が必要な仕様は推測で書かず、公式ドキュメントか実機の出力で確認する。
- 確認できなかった点は `docs/plan.md` の未確認事項へ追記する。
