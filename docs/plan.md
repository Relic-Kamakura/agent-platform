# 実装計画

G4 向け AI エージェント開発基盤ひな形。競合リサーチエージェントをサンプル題材とする。
本ファイルは進捗管理の唯一の正とする。各 Phase 完了時にチェックを更新する。

- ステータス: **全 20 章（00〜19）+ 付録の実装完了。実機確認は各章のハンズオン内で実施する**
- 最終更新: 2026-08-23

## 既定モデルを Haiku 4.5 に統一（2026-08-23）

学習時の実行コストを抑えるため、教材全体の既定モデルを安価な Haiku 4.5 に統一した
（Bedrock 単価: 入力 $1 / 出力 $5 per 100万トークン。Anthropic 発表と料金集計サイトで裏取り。
リージョンにより 1 割高の場合あり）。

- ID は実機一覧で確認した **`us.anthropic.claude-haiku-4-5-20251001-v1:0`**（日付付きのみ。
  Sonnet 4.6 のような短縮 ID は存在せず、当初の `us.anthropic.claude-haiku-4-5` は
  ValidationException になった）。Converse スモークテストで応答を確認済み（in=23 / out=51）
- 対象: 第1・2章の exercises / solutions、第1章の料金例と 02_count_tokens の単価
  （$3/$15 → $1/$5）、15-mcp の既定（古い `apac.` 接頭辞も `us.` に統一)、
  07-full-app の 3 役割の既定、cdk.json の modelIds と region
- **東京の Haiku 4.5 は `apac.` ではなく国別 `jp.` プロファイルのみ**（実機一覧で確認）。
  これに伴い本体の既定リージョンを us-east-1 に変更し、`jp` / `global` を
  既知接頭辞に追加。東京で使う場合は `BEDROCK_MODEL_ID_PREFIX=jp` を明示する
- 07-full-app の役割別変数（ORCHESTRATOR / SEARCH / REVIEW）は維持。実案件で
  orchestrator / review を上位モデルに差し替えるための分割で、第5章の解説も
  「既定は全役割 Haiku、差し替えの判断材料」を示す形に改訂
- Phase 0 の環境変数表（MODEL_ID_ORCHESTRATOR = Sonnet 系）は当時の設計記録として残すが、
  既定値は本エントリが上書きする

## ハンズオン方式の変更: 穴埋め方式（2026-08-23）

ハンズオンの標準を**穴埋め方式**に変更した。学習者が修正するコードを solutions とは
別の章直下 `exercises/` に TODO 付きの骨組みとして置き、コード修正 → 実行で
学ぶべきことを体験させる。

- README は解説節（N.1 概要）に TODO を埋めるための具体構造（コード断片）を置き、
  ハンズオン節の末尾に開閉式（`<details>`）の解答例を付ける
- verify は「TODO が残っていれば該当節を案内して fail / solutions を exercises に
  適用すれば全パス」のラウンドトリップを守る
- あわせて**ハンズオンの章内完結を恒久ルール化**（2026-08-23、writing-style.md に明文化）。
  編集・実行するファイルはすべて章内に置き、本体 07-full-app は読み比べの対象とする
- 適用状況: **第1〜3章に適用済み**（第1章: exercises 3 本 + verify 3 件 /
  第2章: exercises 3 本 + verify 6 件。第2章は既定値も us-east-1 / Sonnet 4.6 に統一し、
  botocore[crt] を同梱 / 第3章: 章内完結の uv プロジェクト化。exercises/fetch_page.py の
  TODO 4 つを埋め、章直下の 01_/02_ スクリプトで動かし、章内 pytest 7 件で判定。
  第3章は本体 07-full-app への参照を持たない完全独立の章とした。
  fetch_page の完成品は本体に同梱してあり、第6章はそれをテスト対象にする）。
  第4章以降は順次移行する（本体を改造する旧方式の章は移行時に章内完結へ改める）。
  移行完了時に root README と writing-style.md の旧方式（写経/要件実装）の記述を整理する

同日、第1章を実機ハンズオンの結果に合わせて再構成した。実在確認（list-inference-profiles）を
先頭の 1.3 に移動、接頭辞リゾルバ実装のハンズオンは削除して解説（1.1.6）に縮約、
トークン計測（1.5）とストリーミング（1.6）のハンズオンを追加。既定値は実機確認済みの
us-east-1 / `us.anthropic.claude-sonnet-4-6` に変更し、`botocore[crt]` を章の
pyproject に同梱した。遭遇した事象（crt 欠如 / ValidationException / Legacy モデル拒否）は
troubleshooting.md に記録済み。

## AWS 接続済み前提化（2026-08-22）

AWS には接続済みであることを教材全体の暗黙の前提とした（接続手順・Sandbox への言及も
教材には書かない）。これに伴い:

- 「要 AWS」「AWS 不要」「未認証ならスキップ」等の要否記載を全章の README・verify から削除。
  ハンズオン節の見出しはすべて `【ハンズオン】` に統一（writing-style.md も同期）
- `docs/aws-checklist.md` を廃止（「認証復旧後にまとめて回収する」という前提ごと不要になった。
  実機確認は各章のハンズオンをその場で実施する）
- 合格判定（verify）が AWS 認証なしで通る設計自体は維持している。CI や認証切れ時にも
  判定だけは回せるようにするための技術的性質であり、学習者向けの案内からは消した

## 章再編（2026-08-20）

全章の README を「概要 → 実装のポイント → 【ハンズオン】 → まとめ」の固定構成に改訂した
（手本は 01-invoke-bedrock。規定は writing-style.md「章の構成」と CLAUDE.md に同期。
章末まとめ節を総括禁止の例外として明文化）。ハンズオンのコード・コマンドは不変で、
verify の節番号参照はメッセージ文字列のみ追従した。

- 第10章 `10-knowledge-base`（ナレッジベース / RAG）を新設。写経方式の独立 uv プロジェクトで、
  チャンク分割 → 2-gram スコア → 上位 k 取得のミニ RAG を自作する。verify 6 件は AWS 不要、
  Knowledge Bases の Retrieve 実機確認は aws-checklist に追加。これに伴い旧 10〜18 章を
  11〜19 章へ繰り下げ（横断ドキュメント・verify・solutions の参照も追従済み）
- 学習内容が直接伝わる章名へ改名: `02-first-agent`→`02-agent-loop`、
  旧 `11-frontend`→`12-streaming`、旧 `13-security`→`14-prompt-injection`
- ラウンドトリップ再確認: 01（7 passed）/ 02（6）/ 03（6）/ 10（6）、07-full-app のテスト 38 件全パス。
  aws-checklist の節参照は全行を新番号に更新（13.4→14.5 等、従来からのズレ 2 件も修正）

## 全章作成（2026-08-16）

進め方の標準「読む → 書く → 動かす → 判定」を明文化し（root README / writing-style.md）、
第10〜18章と 99-appendix を作成した。これに伴い:

- Phase 3 の実装は第10章（AuthStack + JWT authorizer 配線。solutions 完備・synth 検証済み）
- Phase 4 の実装は第11章（Next.js + Route Handler + ストリーミング。tsc 検証済み。
  本体には orchestrator の on_stage コールバックと src/streaming.py を追加、テスト 38 件）
- Phase 5 の実装は第12章（evals ハーネス）と第13章（インジェクション fixture + 耐性 eval）
- 第1・2章は写経方式（章独立 uv プロジェクト）に改修、第8章に自作 Dockerfile 演習を追加
- 全章の verify を「未実施 = 案内付き fail / 模範解答 = 全パス」のラウンドトリップで検証済み
- デプロイ・実モデル呼び出しを伴う確認は docs/aws-checklist.md の 12 項目に集約

## リポジトリ再編（2026-08-15）

技術ごとの章立てをルート直下のディレクトリ構造にした。詳細は README.md。

- `agent/` → `07-full-app/`、`infra/` → `09-infra-as-code/` に改名（テスト・synth とも再編後に全パス確認済み）
- 空だった `frontend/` `evals/` は削除。実体は各 Phase 完了時に章として追加する:
  **Phase 3 → `10-auth/`、Phase 4 → `11-frontend/`、Phase 5 → `12-evaluation/` と `13-security/`**
- 章 00〜09 を作成。各章 = README（技術解説）+ exercise.md + verify/（機械判定）+ solutions/
- 2026-08-15 追記: 章名を「何が学べるか」が伝わる名称に全面改名
  （00-dev-environment / 01-invoke-bedrock / 02-first-agent / 03-tool-design / 04-cost-control /
   05-multi-agent / 06-agent-testing / 07-full-app / 08-agentcore-deploy / 09-infra-as-code）。
  README 全 11 本を docs/writing-style.md（AI 臭除去 + Diátaxis 準拠の文章ガイド。参考記事を調査して作成）に沿って書き直した
- 2026-08-15 再改訂: 「段落 2〜4 文まで + 列挙は箇条書き」のバランス規定を writing-style.md に追加し、
  README 全 11 本を再度書き直し（各 60〜90 行）。AgentCore Runtime の仕様値
  （microVM 分離 / 同期 15 分・ストリーミング 60 分・非同期 8h / ペイロード 100MB）と
  クロスリージョン推論の仕様（地理内ルーティング / 呼び出し元リージョン単価 / 宛先リスト不変）を
  AWS 公式ドキュメントで裏取りして反映。ReAct (Yao et al. 2022) / CoT (Wei et al. 2022) の出典を明記。
  ※文章ルールはユーザー恒久指定: AI 臭排除は常時、簡潔で見やすく、仕様値は裏取り必須
- 2026-08-15 再々改訂: 構成を agentcore-book (minorun365) の型に統一。
  `# 第N章` + `## N.x` の番号付き節、`【ハンズオン】` 節にコピペ可能なコマンドを 1 ブロック 1 実行単位で配置、
  exercise.md は README に統合して廃止、実行スクリプトは章直下の連番ファイル
  （01-invoke-bedrock/01_invoke_model.py 等）に移動
- すべての verify は「未実施 = 案内付き fail / 模範解答適用 = 全パス」を検証済み

---

## 0. 前提となる調査結果（確認済みの事実）

設計の根拠。ここに書いた事実は一次情報で確認済み。

| 事実 | 出典 |
| --- | --- |
| AgentCore Runtime のコンテナ契約は `linux/arm64` / `0.0.0.0:8080` / `POST /invocations` / `GET /ping` | AWS AgentCore devguide (runtime service contract) |
| `bedrock_agentcore.runtime.BedrockAgentCoreApp` がこの契約を実装する。`@app.entrypoint` を書くだけでよい | Strands 公式 deploy ガイド |
| AgentCore Runtime は **ap-northeast-1（東京）で利用可能**。Memory / Gateway / Identity / Observability も東京対応 | AWS AgentCore devguide (supported regions) |
| ~~CDK に stable な L2 `Runtime` がある~~ → **誤り。Phase 2 で実機確認し否定した**。2.264.0 は L1 のみ | 当初: Web の解説記事 / 訂正: `node_modules` の型定義 |
| **CDK の既知の罠**: ECR リポジトリと Runtime を同一 deploy で作ると、ECR が空のため Runtime 作成が失敗する | 複数の実装レポート |
| Strands の `BeforeToolCallEvent` は「ツール呼び出し回数の制限」を公式ユースケースとして挙げている（`event.cancel_tool` で中断） | Strands hooks ドキュメント |
| トークン消費は `result.metrics.accumulated_usage["totalTokens"]`、ループ回数は `result.metrics.cycle_count` で取得できる | Strands metrics ドキュメント |
| セッション ID は 33 文字以上必要 | Strands 公式 deploy ガイド |

### 未確認事項の検証結果（Phase 1–2 で確定）

- [x] **CDK に L2 `Runtime` は存在しない。** aws-cdk-lib 2.264.0 の `aws-bedrockagentcore` は
      L1 (`Cfn*`) のみ。Web 記事の「stable な L2 がある」という記述は誤り。`CfnRuntime` を使う
- [x] **VPC を使わない指定は `networkConfiguration: { networkMode: 'PUBLIC' }`**。
      `CfnRuntime.NetworkConfigurationProperty` の型定義で確認
- [x] **JWT authorizer は `CfnRuntime` から設定できる。**
      `authorizerConfiguration.customJwtAuthorizer` に `discoveryUrl`（必須）/ `allowedClients` / `allowedAudience`
- [x] **Strands 1.52.0 に `max_turns` 相当は無い。** `Agent.__init__` の全引数を確認済み。
      `BeforeModelCallEvent` で自前実装した（`src/guards.py`）
- [x] **推論プロファイル接頭辞の導出規則を確定。** `ap-northeast-1` → `apac`。
      `strands.models.bedrock._get_default_model_with_warning` のソースと同じ規則を `config.py` に実装
- [ ] 東京リージョンで使用する Claude モデルの推論プロファイル ID（`apac.` プレフィックスの要否）
      → **本セッションでは実機確認しない方針で合意**。根拠コメント付きの暫定デフォルトを置き、
      利用者が `aws bedrock list-inference-profiles --region <region>` で確認して `.env` を直せる形にする。
      `README.md` と `scripts/check_env.sh` にこの確認手順を必ず含める

---

## 0.5. Phase 0 で確定した設計判断

| 論点 | 決定 | 理由 |
| --- | --- | --- |
| Web 検索プロバイダ | **`mock` を既定、`SEARCH_PROVIDER=tavily` で実検索に切替** | API キーなしでローカル実行とテストが即通る。ハンズオンの再現性を最優先する要件に沿う。Bedrock 経由の Claude にはサーバサイド web_search が無いため、外部 API か mock が必須 |
| ReviewAgent の配置 | **`orchestrator.py` のコードで決定的に最後に 1 回実行**（SearchAgent のみ agents-as-tools） | 検証をモデルの裁量で省略させない。教材として「どこを非決定に委ね、どこをコードで固定するか」を示せる |
| フロントからの呼び出し経路 | **Next.js Route Handler（サーバ側）で JWT 検証 → AWS SDK で `InvokeAgentRuntime`** | AWS 認証情報をブラウザに出さない。JWT 検証が自前コードとして可視化され、`AUTH_BYPASS` もここに置ける |
| モデル ID の実機確認 | 本セッションでは行わない | 上記の未確認事項として明示的に残す |

---

## 1. 未確定事項の外出し方針

### 原則

1. **コードにリテラルを書かない。** リージョン / ロール ARN / モデル ID は必ず設定層を経由する。
2. **設定層は 1 箇所に集約する。** Python は `agent/src/config.py` の `Settings`（pydantic-settings）だけが `os.environ` を読む。CDK は `infra/lib/config.ts` の `loadConfig(app)` だけが `node -c` context を読む。
3. **デフォルト値には必ず根拠コメントを書く。** 「なぜこの値か」「何を確認したら変えるべきか」を 1 行で添える。
4. **未確定なものは起動時に検証する。** 空文字や不正形式は `ConfigurationError` で即座に落とす。動いてから気づく状況を作らない。

### 環境変数一覧（`agent/.env.example` に反映）

| 変数 | 既定値 | 根拠コメントに書く内容 |
| --- | --- | --- |
| `AWS_REGION` | `ap-northeast-1` | 東京で AgentCore Runtime が利用可能なことを確認済み。所属リージョンが違う場合のみ変更 |
| `BEDROCK_MODEL_ID_PREFIX` | `apac.` | 新しめの Claude は推論プロファイル経由でのみ呼べる。プレフィックスはリージョングループ（`us.` / `eu.` / `apac.`）。オンデマンド直接呼び出しが可能なら空文字にする |
| `MODEL_ID_ORCHESTRATOR` | Sonnet 系 | タスク分解と統合。判断が要るので上位モデル |
| `MODEL_ID_SEARCH` | Haiku 系 | クエリ生成と検索結果の要約のみ。軽量モデルで足りる |
| `MODEL_ID_REVIEW` | Sonnet 系 | 出力の妥当性判定。誤検知が致命的なので上位モデル |
| `MODEL_ID_*_FULL` | 未設定 | プレフィックス連結を使わず ID を丸ごと指定したい場合の逃げ道 |
| `MAX_TOOL_CALLS_TOTAL` | `12` | 1 リクエストあたりのツール呼び出し総数上限 |
| `MAX_TOOL_CALLS_PER_TOOL` | `6` | 同一ツールの連続呼び出し暴走を止める |
| `MAX_AGENT_TURNS` | `10` | モデル呼び出し（イベントループ cycle）の上限 |
| `SEARCH_PROVIDER` | `mock` | `mock` / `tavily`。既定を `mock` にして API キーなしでローカル実行できるようにする |
| `TAVILY_API_KEY` | 未設定 | `SEARCH_PROVIDER=tavily` のときのみ必須 |
| `HTTP_TIMEOUT_SECONDS` | `20` | 外部 API のタイムアウト |
| `HTTP_MAX_RETRIES` | `2` | 指数バックオフでのリトライ回数 |
| `AUTH_BYPASS` | `false` | 開発時のみ `true`。本番で `true` かつ非ローカルなら起動時に落とす |
| `LOG_LEVEL` | `INFO` | |

### CDK context 一覧（`infra/cdk.json` の `context` に既定値、`-c` で上書き）

| キー | 既定値 | 用途 |
| --- | --- | --- |
| `region` | 未設定（`CDK_DEFAULT_REGION` にフォールバック） | デプロイ先 |
| `agentcoreExecutionRoleArn` | 未設定 | **設定されていれば既存ロールを使う。未設定なら CDK が新規作成する**（両経路を用意する要件への対応） |
| `ecrRepositoryName` | `agent-platform/agent` | |
| `runtimeName` | `agentPlatformAgent` | |
| `imageTag` | `latest` | |
| `modelIds` | 上の Python 側と同じ値 | Runtime の環境変数として注入 |
| `authBypass` | `false` | |

---

## 2. アーキテクチャ方針（要点のみ。詳細は docs/architecture.md）

- **マルチエージェント構成**: Orchestrator が SearchAgent を「ツールとして」呼ぶ（agents-as-tools）。ReviewAgent は Orchestrator の裁量に任せず、`orchestrator.py` のコードで**決定的に最後に 1 回走らせる**。検証をモデルの気分に任せないため。この判断理由はコードコメントと architecture.md に書く。
- **VPC は使わない**。AgentCore Runtime のマネージドネットワークを使う。
- **認証経路**: ブラウザ → Cognito でトークン取得 → Next.js Route Handler（サーバ側）で JWT 検証 → AWS SDK で `InvokeAgentRuntime`。AWS 認証情報をブラウザに出さない。`AUTH_BYPASS=true` で JWT 検証をスキップできる。
- **デプロイ順序**: ECR 作成 → イメージ push → Runtime 作成。CDK の既知の罠を `scripts/deploy.sh` で吸収する。

---

## Phase 0: 設計提示 ✅

- [x] 一次情報の調査（コンテナ契約 / リージョン / CDK L2 / Strands hooks・metrics API）
- [x] `docs/plan.md` 作成
- [x] `CLAUDE.md` 作成
- [x] 未確定事項の外出し方針を提示
- [x] 判断に迷った点を質問として提示
- [x] **ここで停止し、承認を求める**

---

## Phase 1: エージェント本体とローカル実行

- [x] `agent/pyproject.toml`（Python 3.12+, uv, 依存: `strands-agents` / `bedrock-agentcore` / `pydantic-settings` / `httpx` / `pytest`）
- [x] `agent/src/config.py` — `Settings`。環境変数を読む唯一の場所。モデル ID のプレフィックス連結と起動時バリデーション
- [x] `agent/src/errors.py` — 例外定義と、エージェントが読める形へのエラー整形（`to_tool_result()`）
- [x] `agent/src/tools/web_search.py` — 1 ツール 1 責務。docstring を「LLM 向け仕様書」として記述（入力 / 出力 / 含まないもの）
- [x] `agent/src/tools/providers/` — `mock` と `tavily`。タイムアウトと指数バックオフ付きリトライ
- [x] `agent/src/guards.py` — `ToolCallLimiter`（`BeforeToolCallEvent`）と `TurnLimiter`（`BeforeModelCallEvent`）、`UsageLogger`（`AfterInvocationEvent` でトークン数を構造化ログ出力）
- [x] `agent/src/agents/search_agent.py` / `review_agent.py` / `orchestrator.py` — 役割ごとにモデルを分け、割り当て理由をコメントで明記
- [x] `agent/src/main.py` — `BedrockAgentCoreApp` エントリポイント
- [x] `agent/tests/` — 設定バリデーション / 上限ガード / ツール異常系 / mock プロバイダでのオーケストレータ結線
- [x] モデル ID は根拠コメント付きの暫定デフォルトを置き、`config.py` に「プレフィックス連結の結果」を
      起動時ログへ 1 行出す（利用者が実際に何を呼ぼうとしているか一目で分かるようにする）
- [x] **動作確認**: `uv run pytest` が通ること、`uv run python -m src.main` で `:8080` が上がり `curl /ping` が 200、`curl -XPOST /invocations` が調査結果を返すこと

---

## Phase 2: Dockerfile と AgentCore デプロイ

- [x] `agent/Dockerfile` — `--platform=linux/arm64`、uv ベースイメージ、`EXPOSE 8080`
- [x] `agent/.dockerignore`
- [x] `scripts/check_env.sh` — aws cli / docker buildx / uv / node のバージョン、認証情報、リージョンの AgentCore 対応、Bedrock モデルアクセスを検査
- [x] `scripts/deploy.sh` — ECR 作成 → `docker buildx build --platform linux/arm64 --push` → Runtime デプロイの順序を強制するラッパー
- [x] `infra/` の Runtime 部分のみ（ECR スタック + Runtime スタック + 実行ロールの新規作成／既存 ARN の両経路）
- [ ] **動作確認**: ローカルで ARM64 イメージをビルドし `docker run` で `/ping`。その後デプロイし `aws bedrock-agentcore invoke-agent-runtime` で応答を確認

---

## Phase 3: CDK 全体

- [ ] `infra/bin/app.ts`、`infra/lib/config.ts`
- [ ] `AuthStack` — Cognito User Pool / App Client / ドメイン
- [ ] `AgentRuntimeStack` に inbound JWT authorizer を追加（L2 で不可なら `CfnRuntime` に降りる）
- [ ] `FrontendStack` — Amplify Hosting
- [ ] 出力（User Pool ID / Client ID / Runtime ARN）をフロント設定に受け渡す
- [ ] **動作確認**: `npx cdk diff` / `npx cdk deploy --all`、Cognito ユーザ作成 → トークン取得 → Runtime 呼び出しが 200

---

## Phase 4: フロントエンド

- [ ] `frontend/` — Next.js App Router、Cognito ログイン
- [ ] `app/api/invoke/route.ts` — JWT 検証 → `InvokeAgentRuntime`。`AUTH_BYPASS` 対応
- [ ] 調査結果表示 UI（ストリーミング対応の可否は Phase 4 冒頭で判断）
- [ ] **動作確認**: `npm run dev` でローカル、Amplify デプロイ後に本番 URL で 1 往復

---

## Phase 5: evals と docs

- [ ] `docs/learning-roadmap.md` — 習得項目の Tier 分けと習得判定（作成済み。Phase 5 で evals・演習と整合させて最終化する）
- [ ] インジェクション fixture（mock プロバイダ）と耐性 eval ケースの追加（ロードマップ Tier 1-9）
- [ ] `docs/exercises.md` — 演習 5 本（ツール追加 / 上限観察 / ルーブリック強化 / エージェント追加 / 注入耐性）。各演習に合格条件を付ける
- [ ] `evals/cases.jsonl` — 期待条件（含むべき語 / 含んではいけない語 / ツール呼び出し上限 / トークン上限）
- [ ] `evals/run_eval.py` — ローカル実行と デプロイ済み Runtime 実行の両対応、結果表とコスト概算を出力
- [ ] `README.md` — 30 分でローカル実行、60 分でデプロイ
- [ ] `docs/setup.md` / `docs/architecture.md` / `docs/design-template.md`
- [ ] `docs/troubleshooting.md` — **見出し構造のみ。中身は空**
- [ ] **動作確認**: まっさらな環境で README 通りに手順を再現し、所要時間を計測して記録

---

## 判断が必要な事項

進行を止めずに進めたが、方針として確認しておきたいもの。

| # | 事項 | 現状の実装 | 判断してほしいこと |
| --- | --- | --- | --- |
| 1 | ReviewAgent の指摘を受けた自動修正 | verdict が `revise` のとき **1 回だけ** 修正パスを走らせる（`orchestrator.py`）| 修正回数 1 回で良いか。0 回（指摘を添えるだけ）にするか |
| 2 | AgentCore Observability (OpenTelemetry) | 未導入。トークン消費は自前の構造化ログで出している | `aws-opentelemetry-distro` を入れて分散トレースまで取るか。イメージ肥大とコールドスタート増とのトレードオフ |
| 3 | IAM 実行ロールの Bedrock 権限 | モデル ID を差し替え可能にするため `foundation-model/*` と `inference-profile/*` のワイルドカード | ひな形としてはこれで良いか。本番テンプレートとして ID を絞る前提にするか |
| 4 | ECR リポジトリの `removalPolicy` | `DESTROY`（ひな形なので消しやすさ優先） | 教材としてこのままで良いか |
| 5 | `MODEL_ID_SEARCH` の Haiku 系 ID | 未検証の暫定値。`check_env.sh` が実在確認して落とす | 実機確認後、確定値を `.env.example` と `cdk.json` に反映する必要がある |
