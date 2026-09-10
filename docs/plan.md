# 実装計画

G4 向け AI エージェント開発基盤ひな形。競合リサーチエージェントをサンプル題材とする。
本ファイルは進捗管理の唯一の正とする。各 Phase 完了時にチェックを更新する。

- ステータス: **全 20 章（00〜19）+ 付録の実装完了。実機確認は各章のハンズオン内で実施する**
- 最終更新: 2026-09-10

## 修正手順のスキル化とフックによる強制（2026-09-10）

今回のレビューからコミットまでの手順を `.claude/skills/review-and-commit/` にまとめ、教材の修正は必ずこの手順で行うことにした。

- SKILL.md: 着手の宣言（`scripts/start.sh`）→ 守ること（AWS を呼ばない、教材外の資料に言及しない、章内完結、分量、ハンズオンの型、記述式の設問を置かない、分かりにくい語を使わない）→ 確認 → 修正 → 検証 → 文体レビュー（stop-ai-slop-jp）→ plan.md への記録 → 章ごとの 1 文コミット（AI による作成の注記なし、push はしない）
- scripts: `check_links.py`（相対リンク）、`measure_chapters.py`（行数と概要 + ポイントの字数）、`check_text.sh`（他章参照、予告、記述式設問、禁止表現、文中改行）、`check_mermaid.sh` + `check_mermaid.mjs`（mermaid と jsdom で全ブロックを解析）、`verify_roundtrip.sh <章>`（素 = 案内付き fail、一時ディレクトリで solutions 適用 = 全パス）
- `.claude/hooks/require-review-skill.sh` を `.claude/settings.json` の PreToolUse（Edit / Write / MultiEdit / NotebookEdit）に登録した。章ディレクトリ、docs、scripts、ルートの README と CLAUDE.md への編集は、`start.sh` が置くマーカー（`.claude/.review-and-commit.active`、12 時間有効、.gitignore 済み）が無いと exit 2 で止まり、スキルを読むよう案内する。SessionStart でも同じ案内を出す
- CLAUDE.md の「進め方」にこの手順を最上位の規約として追加した。`measure_chapters.py` の現時点の超過は第16章（301 行。2 プロジェクトと 6 本のハンズオンに解答例と期待出力を置いた結果）と第17・19章（各 202 行）

## 全章の章内完結化と分量削減、技術的な誤りの修正（2026-09-10）

構成レビュー（分量・節構成・演習量）と技術レビュー（ライブラリのソースと AWS 公式での照合）を全 21 章に対して行い、その結果を反映した。

**章内完結**: 他章への依存と予告を全廃した。「第N章で学ぶ」「第N章で作った」「第N章 N.x 参照」を各章内の 1〜2 文の説明に置き換え、他章への参照は文末の `## 次の章` リンクだけにした。各章の冒頭にその章のセットアップ（`cd` と `uv sync` / `npm ci`）を置き、第17章にはセットアップ節を新設した。規約として writing-style.md に「章内完結と分量」節を、CLAUDE.md の章の規約に同項を追加した。

**分量**: 概要 + 実装のポイントで日本語 1,200 字以内、README 200 行以内、新出概念 1 章 5 個までを目安にした。演習に要らず実行時に踏まない節を削除（第1章の推論パラメータ詳説とデータ越境、第2章の ReAct テキスト実装と ConversationManager、第4章のオンデマンドとプロビジョンド、第10章のスコーピングマトリクス、第13章の評価対象の詳説、第17章のデプロイ 3 方式とクォータ、第19章の RAG メタデータフィルタ、第20章の CSAT ほか）。全章のハンズオンを `N.x.1 TODO を n 個埋める` → `N.x.2 実行する`（期待結果 + `<details>` 解答例）→ `N.x.3 合格判定` の並びに統一した。200 行に収まらなかったのは第1〜3章と第16章で、コードブロックと解答例が大半を占めるため。

**実行すると壊れていた箇所（本体 07-full-app）**: `str(result.message)` は dict の文字列表現を返すため報告本文が dict になり、ReviewAgent が常に revise を返していた。`src/agents/results.py` の `result_text()` に集約して修正。Orchestrator と SearchAgent を 1 インスタンス共有していたが、Strands の Agent は同一インスタンスの並行実行を ConcurrencyException で拒否し、履歴とメトリクスも混ざる。Agent はリクエストごとに `build_agent()` で作り、`BedrockModel` だけ共有する形に変更した。`MaxTokensReachedException` を捕まえておらず 500 で終わっていたので、途中までの本文を救出して `truncated: true` で返すようにした。`BedrockModel` に `boto_client_config`（読み取りタイムアウトと `max_attempts: 1`）を渡し、タイムアウト後の自動再送による二重生成を止めた。ログから検索クエリと観点の本文を外し、長さだけ記録する。テストは 38 件から 41 件になった。

**各章の技術的な修正**: 第2章のメトリクス（`accumulated_usage` と `cycle_count` は Agent の生涯累計）、第3章の toolSpec の例（`Args:` 節以外は description に入り、properties の description は `"Parameter url"` になる）と httpx の接続失敗の変換、第4章と第15章の「出力上限は例外にならない」の誤り（`MaxTokensReachedException` が送出される）、第5章の専門エージェントの共有インスタンス、第9章の料金例の単価、第10章の閉じタグ無害化を演習として実装、第11章の Gateway のターゲット 3 種、第12章のキャッシュ無効化の範囲（変更点より後ろのキャッシュポイントだけが無効）、第13章の Standard tier と cross-Region の guardrail profile（CLASSIC は英語・フランス語・スペイン語のみで日本語の PROMPT_ATTACK が発動しない）、第14章の `interrupt`、第16章の `greaterThanOrEquals` は number 専用（`published_epoch` を追加）と埋め込み次元の一致と `maxReceiveCount`、第17章の bind 判定（`/.dockerenv` か `DOCKER_CONTAINER` があれば 0.0.0.0）とプロトコルごとのポートとパス、第18章の実行ロール（公式の最小構成へ拡張）と ARN 2 種と VPC モード、第19章の `allowedClients`（Cognito のアクセストークンは `client_id` を持ち `aud` を持たない）、第20章のクライアントのリトライとタイムアウト。

- **aws-cdk-lib 2.264.0 に L2 `Runtime` が存在する**（`aws-bedrockagentcore/lib/runtime/runtime.d.ts`）。`AgentRuntimeArtifact.fromAsset` は deploy 時に CDK がイメージを push するため、ECR を先に作る順序制約が無い。第18章 18.1.1 に 1 段落で追記し、CLAUDE.md の禁止事項にも「この制約は L1 と自前 ECR の構成のもの」と限定を添えた
- リンク切れ 3 件（root README の付録、第7章の troubleshooting、付録の第8章）を修正。通番化の残骸（Dockerfile の「8.4」、verify の「演習 08 / 09」、package.json と uv.lock の章名）も回収した
- 裏取りできず書かなかったこと: MCP で Runtime が `GET /ping` を求めるかどうか、`structured_output` が None になる具体条件、STANDARD tier の対応言語の明示リスト、S3 Vectors と KB の対応リージョン
- 用語の言い換え: 「HTTP 契約」「コンテナ契約」は初見で意味が取れないため、「Runtime がコンテナに要求する条件」「HTTP のエンドポイント定義」のように、その文が指すものを具体語で書く形に置き換えた（AWS との契約を指す「モデルと契約で変わる」は残す）
- 「自分の言葉で答えてください（記述・任意）」の設問（第7章 7.4 確認、第18章 18.3.4）を削除した。機械判定が無く、到達点は手を動かした結果で書く規定に合わないため
- Mermaid 図を古いレンダラでも通る形に統一した（連結矢印を 1 行 1 辺に分割、ノードと辺のラベルを二重引用符で囲む、sequenceDiagram の participant から `<br/>` と括弧を除去）。mermaid 11.17.2 で全 16 ブロックの解析が通ることを確認済み
- 実機確認は未実施（AWS を呼ぶ工程は各章のハンズオンでユーザーが実行する）

## 第20章を第16章に繰り上げ（通番の再割り当て。2026-09-08）

news-kb-mcp を第2部の末尾 16 章とし、第3部を 1 つずつ繰り下げて通番を回復した。対応: 20-news-kb-mcp→16 / 16-agentcore-deploy→17 / 17-infra-as-code→18 / 18-auth→19 / 19-streaming→20。章見出し・節番号・章間参照・ディレクトリ名・package/pyproject の章名を機械置換し、誤置換 2 件（第3章スクリプトと本体 config.py の timeout 20.0）を検出して復旧、hello-agent の応答は `"chapter": 17` に更新。次の章チェーンは 15→16（同じ部）→17（部またぎ）に張り替えた。第0章の CDK 依存手順の cd が部またぎ（1-basic/07 → 3-production/18）で壊れていたのも修正。

## 第20章 news-kb-mcp を追加（2026-09-08）

準備中だった応用編のニュース検索基盤を、ユーザー指定の確定設計に合わせて 1 章に統合して実装した（旧 20-ingest-pipeline / 21-gateway-tools の 2 章案は廃止）。AWS What's New 等の RSS を 6 時間ごとに差分取得して S3 + Knowledge Base（S3 Vectors + Titan Embeddings V2）へ取り込み、AgentCore Gateway（Cognito JWT インバウンド認可）の Lambda ターゲット 2 ツール（search_aws_updates / get_article）を mcp-remote 経由の MCP クライアントから呼ぶ。読み取り側に AgentCore Runtime や回答生成 LLM は置かない。書き込み側と読み取り側は S3 と KB だけを接点にする。

- 章構成: exercises 4 ファイル（fetch_articles.py / tools_handler.py / knowledge-base-stack.ts / gateway-stack.ts）+ 完成品（ingestion-stack.ts、lambda_src の 3 Lambda、初回同期スクリプト、mcp.json サンプル）。合格判定は pytest 14 件 + verify.sh（synth 検査）
- ラウンドトリップ実測済み: pytest は素 = 14 failed（全件 TODO 案内）/ solutions 適用 = 14 passed。verify.sh は素 = 案内付き NG / solutions 適用 = 全 OK
- 裏取り: KB の S3_VECTORS は CloudFormation リファレンスの Allowed values、Gateway の Lambda 入力（event = 引数、ツール名は context.client_context.custom の bedrockAgentCoreToolName、ターゲット名___ 接頭辞）と ToolDefinition の形式は AgentCore devguide（gateway-add-target-lambda）、Retrieve のフィルタ演算子（andAll / equals / greaterThanOrEquals 等）は botocore の bedrock-agent-runtime サービス定義、CfnGateway / CfnGatewayTarget / CfnVectorBucket / CfnIndex は aws-cdk-lib 2.264.0 の型定義（いずれも 2026-09-08 確認）
- S3 通知は同一スタック制約があり、追加キュー（SQS + DLQ）は記事バケットと同じ KnowledgeBaseStack に置いた（IngestionStack と分けるとスタック間循環になることを synth で確認）
- get_article の引数は URL ではなく search_aws_updates が返す s3_key にした（URL → キーの対応表を持たないため。README 20.2.3 に判断を記載）
- 未確認事項（実機確認待ち）: S3 Vectors + KB の実デプロイと対応リージョン（既定 us-west-2）、CfnIndex の nonFilterableMetadataKeys=['AMAZON_BEDROCK_TEXT'] の要否（公開サンプル由来）、Cognito アクセストークン + mcp-remote での Gateway 接続（DCR 未対応のため Claude Desktop 直接続は不可の前提）、StartIngestionJob の同時 1 ジョブ制約の再キュー動作

## 全章ファクトチェック（2026-09-08）

全章の事実主張を、AWS 公式ドキュメント（AgentCore devguide の getting-started-custom / runtime-getting-started / runtime-get-started-cli）、章 venv の strands-agents ソース、本ファイルに記録済みの既往裏取りと突き合わせて照合した。

- 修正 1 件: 09 章の料金例 `PRICE_OUT_PER_MTOK` が通番化の機械置換で 15.0 → 11.0 に壊れていたのを検出し復旧（README と run_eval.py の docstring）
- 要修正として報告 1 件: troubleshooting.md と本ファイル過去エントリの「AgentCore の CDK に L2 は無い」。aws-cdk-lib 本体に L1 しか無いのは正しいが、公式 alpha パッケージ `@aws-cdk/aws-bedrock-agentcore-alpha`（npm で 2.268.0-alpha.0 を確認）に L2 `Runtime` / `Memory` 等が公開されており、「L2 は存在しない」と読める記述には alpha の存在を 1 文添えるべき
- 16.1.3 の AgentCore CLI（create → dev → deploy、CodeZip 既定、内部で CDK）は公式 devguide と一致することを確認
- 16.1.2 のコンテナ契約 3 点は正確だが、protocolConfiguration（MCP は 8000 /mcp 等）の既定時である旨の但し書きを推奨
- 詳細はファクトチェックレポート（Artifact）に記録

## 章番号の通番化と部の再配分（2026-09-07）

3 部制の確定形。第1部 基礎編 `1-basic/` = 00〜07章（コア一式 + 完成形の通読）、第2部 応用編 `2-advanced/` = 08〜15章（テーマ別）、第3部 本番運用基盤 `3-production/` = 16〜19章 + 99-appendix。章番号は部をまたぐ通番に振り直した。対応: 10-knowledge-base→08 / 13-evaluation→09 / 14-prompt-injection→10 / 15-mcp→11 / 16-prompt-caching→12 / 17-guardrails→13 / 18-hitl→14 / 19-structured-output→15 / 08-agentcore-deploy→16 / 09-infra-as-code→17 / 11-auth→18 / 12-streaming→19。ディレクトリ名・章見出し・節番号（N.x）・verify の案内文・章間参照・pyproject の章名を機械置換し、package.json / package-lock.json のバージョン値と 03 章スクリプトの timeout 値に出た誤置換は元に戻した。hello-agent の応答は `"chapter": 16` に更新。本エントリより古いエントリの章番号・ディレクトリ名は当時のまま残している。あわせて第1部に入口 README を追加し、環境構築が章内で完結しない 2 章を直した（09 章に本体の `uv sync --project` を明記、16 章に Docker の確認だけで始められる旨を明記）。

## 2 部制 → 3 部制への再編（2026-09-07）

教材を第1部 基礎編（`1-basic/` = 00〜03章。エージェントのコア）、第2部 応用編（`2-advanced/` = エージェントの中身の発展章 04〜07・10・13〜19 と付録）、第3部 本番運用基盤（`3-production/` = 08・09・11・12章。エージェントを外へ届ける側）の 3 部制にした。外部レビューの「本番運用基盤をエージェント開発の主題から切り離す」指摘への対応で、章番号は振り直さず部内の非連続を許容した。応用編には AWS アップデート情報の収集と検索を題材にした 20-ingest-pipeline（RSS 差分取得 → S3 → SQS → StartIngestionJob → KB）と 21-gateway-tools（AgentCore Gateway + Cognito JWT + Retrieve のメタデータフィルタ）を追加予定（実体は設計確定後に追加。空の章ディレクトリは作らない。入口は 2-advanced/README.md）。

- 追随修正: root README / CLAUDE.md / docs / pyrightconfig.json / scripts（check_env.sh と deploy.sh のパス）/ 各章 README のルートから実行するコマンド（`cd NN-*` を `cd 1-basic/NN-*` 等にする）
- 部の中では章間の相対参照（`../07-full-app` など）が同階層のまま成立する。部をまたぐ参照は、第3章の次の章リンク、第1章 verify の 07-full-app import（conftest.py の APP_DIR）、07→08・09→10・10→11・12→13 の次の章リンク、第8章 verify.sh の本体イメージビルドパスを修正した
- 各章の `.venv` は絶対パスを内包するため移動で無効になる。`uv run` 時に uv が作り直すが、失敗する場合は `rm -rf .venv && uv sync`（troubleshooting.md の既存項目）
- 応用編の設計で先に裏取りが要る点: S3 Vectors を KB のベクトルストアにする手順と対応リージョン、AgentCore Gateway の Lambda ターゲットと Cognito JWT 認可の IaC 対応、StartIngestionJob の同時実行制約

## 公式ベストプラクティスに沿った見直し（2026-08-30）

AWS ブログ「エンタープライズにおける AI エージェント: AgentCore を活用したベストプラクティス」と
クォータページを一次情報として、第5・6・7・8・9・13章を見直した。数値は versions.md に集約。

- 第9章から L1 / L2 の議論を削除。aws-cdk-lib 2.264.0 の `aws-bedrockagentcore` には
  L2 `Runtime` / `RuntimeEndpoint` / `RuntimeAuthorizerConfiguration.usingJWT()` が実在し
  （`lib/runtime/runtime.d.ts` で確認）、旧記述「L1 のみ」は誤りだった。CfnRuntime のまま
  L2 の有無を主題にしない形に改め、troubleshooting / versions からも該当記述を削除
- 第8章に 8.1.3 デプロイ方法の選択、8.1.4 クォータを追加。microVM 分離は公式ドキュメントで確認
- 第5章 5.2.3 に「コードで確実に求まる値をツールにしない」と日付取得の比較、
  第13章 13.2.1 に評価指標 5 つと目標値の参照を追加
- 第6章の要件を 7 本以上・観点 5 つに引き上げ（第3章 verify の 7 本に揃えた）。第7章に 7.4 確認を新設
- [未確認] 「AgentCore の CDK モジュールは experimental」はパッケージ内（.d.ts / README）に注記が無く
  確認できなかった。クォータの「エンドポイントあたりのレート」は公式ではアカウント単位の共有値のみ

## ハンズオン節の見出しラベルの変更（2026-08-30）

ハンズオン節のラベルを `【ハンズオン】` から `ハンズオン: ` に変えた（大見出しのみ。N.x.y には付けない）。見出しは関数名やファイル名ではなく、その節で学ぶ対象で書き、動詞は「実装する」を基本にする。規定は writing-style.md「章の構成」に同期。過去のエントリにある `【ハンズオン】` は当時の記録として残す。

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

## 学習者が読む Python ファイルの文章見直し（2026-08-29）

README と同じ 5 基準を、exercises / solutions / 章直下スクリプトの
docstring・TODO コメントにも適用した。コードと変数名は変更していない。

- 比喩・口語: 「イベントを手で流す」→ 渡す、「エージェントを走らせる」→ 実行する、
  「revise に倒す」→ revise 扱いにする、「頭打ちにする」→ 上限で止める、
  「壊れた入力」→ 形式の違う入力、「pytest で回す」→ 実行する
- 界隈語: 「束縛した」→ 固定した（fetch_page / web_search のファクトリ 5 箇所）、
  「生のテキスト / 生の検索結果」→ 取得した〜、「素の関数」→ 元の関数
- 教材事情: hello-agent の「学習用ミニエージェント」→「コンテナ契約を確かめるための最小エージェント」
- 読者の代弁: 01 章 02_count_tokens の TODO(2)「〜が読み取れる」→ 事実の記述に変更
- 07-full-app の src/tools と tests にも同じ語が入っていたので同期した。
  `uv run pytest` 38 件パスを確認。章 verify も素の状態の fail 内容が変わらないことを確認
- **`07-full-app/src/errors.py` と `providers/base.py` の「握りつぶさない」は残した。**
  CLAUDE.md の規約と docs/learning-roadmap.md の習得判定が同じ語を使っており、
  ここだけ変えると規約と実装のコメントがずれるため

## 初見の読者向けの文章見直しを全章に適用（2026-08-29）

比喩・擬人化の排除、界隈語の置き換え、目的を指す見出し、初出用語の補足、
読者の行動に繋がらない記述の削除、の 5 基準で全 README を通した。
規定は writing-style.md「書いてはいけないもの」に追記済み。

- 比喩・擬人化: 「静かに壊れる」「revise に倒す」「握りつぶす」「頭打ちにする」
  「素通し」「地続き」「受け皿」「膨らむ」「束ねる」「増殖」「掴む」「逃がす」
  「寄せる」「効く」を起きていることの記述に置換。
  「流す」「叩く」「回す」「走らせる」は「渡す」「呼ぶ」「実行する」に統一
- 界隈語: 「生 HTML」→ 取得した HTML、「素の性能」→ モデル単体の性能、
  「型」（形式の意味）→ 形式、「結線」→ 呼び出し、「近道です」→ 分かりやすくなります
- 見出し: 3.2.3 / 3.2.4 / 5.2.3 / 19.1.2 / 19.2.2 / 19.2.3 / 19.3.1 /
  2.1.2 / 4.1.2 / 7.1.2 / 12.1.2 / 13.2.3 / 14.1.2 / 14.1.3 / 14.2.1 /
  15.1.2 / 16.1.1 / 17.2.1 / 17.2.2 / 5.3.2 / 0.2.5 / 6.3.2 / 8.3.3 /
  13.3.3 / 18.3.2 / 4.3.2 を、テーマ名か読者が知りたいことに書き換え
- 初出用語: Pydantic（19.1.1）、スニペット（3.3）、toolUse（3.3.4）、
  inputSchema と toolSpec の対応（5.3.2）に 1 文の説明か章番号を追加
- 削除: 書き手の経験談（0.2.3 / 6.2.2 / 7.2 / 8.1.2 / 9.1.2）、
  教材の運営事情（5.2.1 の「学習コストを抑えるため」）、
  読者の判断の代弁（5.3.2 / 16.1.2）、3 回目の重複説明（5.3.4）、
  冒頭の到達点と同文のまとめ（5.4）
- 敬体と常体の混在（6.1.1 / 9.2.4 / 9.4 / 12.6 / 13.6 / 18.4 / 19.1.2）を敬体に統一
- README のみの変更。pytest 系 12 章の verify を実行し、素の状態の fail 内容が
  変更前と一致することを確認した

## 表と箇条書きの制限を全章に適用（2026-08-29）

ユーザー指定の書き方ルール（回答側は memory/response-style.md）のうち、教材にも効くものを
writing-style.md に追記し、全 README に適用した。

- 追記した規定: 箇条書きは独立した並列項目が 3 つ以上あるときだけ、1 項目 1〜2 行。
  表は列 3 つまで、セルは 20 字まで（コード識別子は除く）。超える説明は表の直後に段落で書く
- 表を書き直した章: 01（4 表）/ 02 / 03 / 04（3 表）/ 07 / 14（2 表）/ 17 / 99 / root README。
  セルから出した説明はすべて表の直後の段落へ移し、情報は落としていない
- 箇条書きを段落にした章: 00 / 01 / 02 / 06 / 08 / 09 / 11 / 12 / 13 / 17 / 99
- 残っている 20 字超のセルはコード識別子（`BeforeInvocationEvent`、
  `src/agents/orchestrator.py` など）と root README のリンク記法のみ

## 中・低優先の用語の章別割り付け（2026-08-29）

2026-08-24 で未着手だった用語を、その技術に手を触れている章の本文へ割り付けた。
独立した「コラム」節は作らない（章の固定構成に無く、読み飛ばされるため）。
用語だけのものは付録の用語集へ寄せた。仕様値は公開ドキュメントのみで裏取りし、
AWS アカウントへの接続はしていない。

- 第1章: 1.1.3 に推論パラメータの表（maxTokens / temperature / topP / stopSequences。
  temperature と topP は片方だけ動かす。ペナルティ系は additionalModelRequestFields 経由）。
  **stopSequences の個数上限は数値を書いていない**（2026-08-24 の「最大 2,500 件」は再確認できず、
  Converse API リファレンスの記載と食い違う可能性があるため数値を落とした）。
  1.1.4 コンテキストウィンドウと最大出力を新設（Haiku 4.5 = 200K / 64K。stopReason での切断検出）。
  1.1.7 オンデマンドとプロビジョンドスループットを新設（バッチを含む 3 形態。バッチの割引率は
  数値を書かず料金ページへ誘導）。1.1.8 にデータ所在の話を追記。
  旧 1.1.4〜1.1.7 は 1.1.5〜1.1.9 へ繰り下げ、章内・第2章・第10章・exercises/solutions の参照も追従
- 第2章: 2.1.3 に停止シーケンス（手書き ReAct が `Observation:` を自演する問題と、
  Strands で不要な理由）。2.1.4 会話履歴とコンテキストウィンドウを新設
  （SlidingWindowConversationManager が既定で直近 40 メッセージ。venv のソースで確認）
- 第4章: 4.1.3 上限を掛けられる場所を新設（maxTokens を第一手に、上限は金額へ翻訳、
  バッチへの逃がし方）。旧 4.1.3 は 4.1.4 へ
- 第7章 / root README: 開発工程と章の対応図は root README に置き、第7章 7.2.1 から参照する
  （7.2.1 のファイル対応表と二重管理にしないため）。
  セキュリティスコーピングマトリクスの第7章への再掲は 14.1.4 と重複するので入れない
- 第8章: 8.1.1 に「実行基盤の選択と推論キャパシティの選択は別軸」を 1 段落
- 第9章: 9.2.2 に Bedrock のリソース ARN が 2 種類要る話（クロスリージョン時は
  ルーティング先リージョンの foundation-model も必要。既存コードの 3 行の意味づけ）。
  9.2.3 CDK に入れておく統制を新設（Guardrail のバージョン固定 / CloudTrail と
  モデル呼び出しログの守備範囲 / VPC エンドポイント）。旧 9.2.3 は 9.2.4 へ
- 第10章: 10.1.3 埋め込みと次元数を新設（Titan Text Embeddings V2 の 1024/512/256。
  **実測ハンズオンにはしない**。この章のミニ RAG は埋め込み API を使わず verify も AWS 非依存で、
  実測を入れると章の独立性が壊れるため）。10.2 に KB のポイズニング（注入の入口は取り込み元、
  一度入ると残り続ける、防御は取り込み側）。旧 10.1.3 は 10.1.4 へ
- 第11章: 11.2.3 エージェントの権限と呼び出したユーザの権限を新設
  （実行ロールは最弱ユーザ基準、RAG では Retrieve のメタデータフィルタで閲覧権限を反映）
- 第12章: 12.5 に CSAT の導線（親指評価を request_id と紐付ける。後付けが効かない理由）
- 第13章: 13.1.2 に Git と Bedrock Prompt Management の使い分け（誰が編集するかで決まる）。
  13.2.2 にモデル評価ジョブとの棲み分け（測る対象がモデル単体。モデル差し替えの判断材料）。
  13.6 に CSAT との関係を 1 段落
- 第14章: 14.2.1 にジェイルブレイク検知は補助という位置づけ。
  14.2.3 に区切り文字の限界（閉じタグを攻撃側も書ける。タグ名のランダム化など）
- 第17章: 17.2.4 フィルタの強度をどう決めるかを新設
  （NONE〜HIGH、入出力別、INSULTS / MISCONDUCT の誤遮断、evals のケースで誤遮断率を測る）
- 第19章: 19.2.2 に maxTokens による切断で structured_output が None になる話
- 付録: `## E. 用語集` を新設（Kendra / SageMaker JumpStart / AWS Artifact /
  DataZone とデータリネージ / SageMaker Model Monitor）。root README の章一覧も追従
- 変更は README のみ。各章の verify は不変で、素の状態（exercises に TODO が残る状態）の
  fail 内容が変わらないことを 01 / 02 / 04 / 10 で確認した

## 認定範囲の用語の組み込み（2026-08-24）

生成 AI 系の認定範囲に近い用語群を「既存の扱い / 組み込み先 / 重要性」で棚卸しし、重要性が高い 7 件を
既存章に組み込んだ（仕様値はすべて公開ドキュメントで裏取り。AWS アカウントへの接続はしていない）。

- 第1章 1.1.3: 推論パラメータ（maxTokens / temperature / topP / stopSequences。stopSequences は最大 2,500 件、
  ペナルティ系は共通パラメータに無く additionalModelRequestFields 経由。Converse API リファレンス）。
  1.1.4: コンテキストウィンドウと最大出力（Haiku 4.5 = 200K / 64K。Anthropic モデル一覧）
- 第14章 14.1.4: Generative AI Security Scoping Matrix（5 スコープ。この教材はスコープ 3）。
  14.2.1: ジェイルブレイクとポイズニングの位置づけ。14.2.2: Guardrails が toolResult を評価しない仕様
  （公式ドキュメントの評価対象表）を、プロンプト層が要る根拠として追記。
  14.2.3: 区切り文字（Anthropic の XML タグ推奨）。fixture を `<search_result>` タグで囲み、
  解答例のプロンプトも同期。verify は不変で 5 passed を再確認
- 第17章 17.2.3: Guardrail の適用点（guardrailConfig、評価対象と非対象の表、stopReason=guardrail_intervened、
  どの役割のモデルに掛けるか）
- root README: エージェント開発の工程と章の対応図
- 中・低優先の用語（Kendra、次元数、オンデマンド推論の対比、Prompt Management / 評価ジョブ、
  フィルタリングポリシー、セキュリティコントロールの俯瞰、JumpStart、AWS Artifact、DataZone、
  データリネージ、モニタリングジョブ）は未着手。中は既存章への追記、低は付録の用語表が候補
  → 2026-08-29 に全件着手。下のエントリを参照
- **[訂正] 第1章の 1.1.3 推論パラメータ / 1.1.4 コンテキストウィンドウと root README の工程図は、
  本エントリでは実際には入っていなかった**（後の章再構成で落ちたか、記載のみで未実施）。
  2026-08-29 のエントリで入れ直した。第14章・第17章の追記は実在を確認済み

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
  第4章も適用済み（章内完結の uv プロジェクト化。CostLimiter を exercises の穴埋みで実装し、
  イベントを手で流す 01 スクリプトで動かし、章内 pytest 5 件で判定。旧「本体 guards.py に追加」は廃止。
  BeforeModelCallEvent.cancel は理由文字列がそのまま最終応答になる打ち切り型であることを
  Strands ソースで確認し、cancel_tool との使い分けとして 4.2.2 に明記）。
  **2026-08-24 に全章の移行が完了した。** 第5〜19章もエージェント並行作業で
  穴埋め + 章内完結に改修（05: 章内ミニ agents-as-tools / 06: 章内同梱の fetch_page にテスト /
  08: hello-agent Dockerfile の TODO 化 / 09: 章 = CDK 本体のため手順 + 解答例形式 /
  11・17: 章内ミニ CDK プロジェクト化で他章への編集を全廃 / 12: exercises/route.ts /
  13: exercises/judges.py + ケース追記例を solutions に追加 / 14: 章内 fixture と
  hardened_prompt、13 章ハーネスへの依存を撤廃 / 15: server.py の TODO 化 /
  16: cached_agent(CacheConfig は実在 API を確認、最小キャッシュ長 4096 トークンは一次情報で裏取り) /
  18: approval_gate / 19: 構造化出力ミニ実装、strands 1.53 で agent.structured_output() が
  非推奨のため structured_output_model 引数の現行 API を採用）。
  全章で「素 = 案内付き fail / solutions 適用 = 全パス」のラウンドトリップを実測済み。
  root README・writing-style.md・CLAUDE.md の旧方式（写経/要件実装・本体改造）の記述も整理した。
  [未確認] 04 章 02_agent_with_limit.py（実エージェントでの打ち切り観察）は
  AWS セッション切れで実測未実施。挙動はソース裏取り済みだが、再認証後に 1 回実行して確認する

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
| **CDK の既知の罠**: ECR リポジトリと Runtime を同一 deploy で作ると、ECR が空のため Runtime 作成が失敗する | 複数の実装レポート |
| Strands の `BeforeToolCallEvent` は「ツール呼び出し回数の制限」を公式ユースケースとして挙げている（`event.cancel_tool` で中断） | Strands hooks ドキュメント |
| トークン消費は `result.metrics.accumulated_usage["totalTokens"]`、ループ回数は `result.metrics.cycle_count` で取得できる | Strands metrics ドキュメント |
| セッション ID は 33 文字以上必要 | Strands 公式 deploy ガイド |

### 未確認事項の検証結果（Phase 1–2 で確定）

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

- [x] 一次情報の調査（コンテナ契約 / リージョン / Strands hooks・metrics API）
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
- [ ] `AgentRuntimeStack` に inbound JWT authorizer を追加（`CfnRuntime` の `authorizerConfiguration`）
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
