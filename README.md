# agent-platform

AI エージェント開発を、動くコードを改造しながら習得するリポジトリです。
番号付きディレクトリが章で、00 から順にこなすと競合リサーチエージェントを題材に
モデル呼び出し → エージェント → ツール → コスト制御 → マルチエージェント → テスト →
コンテナデプロイ → IaC を一周できます。分量は 2〜3 日。

読むだけの章はありません。すべての章が同じ流れで進みます。

1. **読む** — README の解説節で仕組みと理由を理解する
2. **書く** — 【ハンズオン】で、その技術を自分の手でコードとして実装する
3. **動かす** — 実行して「〜が出るはずです」と照合する
4. **判定** — verify が機械的に確認する。通った状態 = その章を「説明できて、書けて、動かせた」

「書く」には 2 つの方式があります。序盤の章は README がコードを段階的に提示し、
それを自分の手で写して動かす**写経方式**（章ディレクトリが独立した uv プロジェクトに
なっています）。型を覚えた後の章は、要件と判定テストだけを与えて自力で書く
**要件実装方式**です。どちらも完成形が `solutions/` にあります。

## 始め方

1. fork するか個人ブランチを切る（ハンズオンで本体 `07-full-app/` を書き換えるため）
2. `00-dev-environment/README.md` を開き、指示どおりに環境を作る
3. 以降は番号順。詰まったら各章の `solutions/` を見てよい
4. AWS 認証が無い間は要 AWS の確認を飛ばしてよい。復旧したら
   [docs/aws-checklist.md](docs/aws-checklist.md) の順にまとめて回収する

```bash
# 合格判定の例（章によっては verify.sh）
uv run --project 07-full-app pytest 03-tool-design/verify -q
```

## 章の一覧

| 章 | 学べること |
| --- | --- |
| [00-dev-environment](00-dev-environment/) | uv / Docker / AWS CLI で開発環境を整える |
| [01-invoke-bedrock](01-invoke-bedrock/) | Bedrock で Claude を呼ぶ。クロスリージョン推論とモデル ID の解決 |
| [02-agent-loop](02-agent-loop/) | エージェントループの仕組み。ReAct と CoT を実物のログで理解する |
| [03-tool-design](03-tool-design/) | ツール設計。docstring 仕様書・エラー設計・リトライ |
| [04-cost-control](04-cost-control/) | hooks による上限とトークン計測。暴走を仕組みで止める |
| [05-multi-agent](05-multi-agent/) | 役割分割とモデルの使い分け。裁量とコードの境界 |
| [06-agent-testing](06-agent-testing/) | LLM を呼ばないエージェントのテスト |
| [07-full-app](07-full-app/) | 完成形の通読（演習の改造対象） |
| [08-agentcore-deploy](08-agentcore-deploy/) | AgentCore Runtime のコンテナ契約・ARM64・デプロイ |
| [09-infra-as-code](09-infra-as-code/) | CDK。IAM ロール設計とデプロイ順序 |
| [10-knowledge-base](10-knowledge-base/) | RAG の仕組みと Bedrock Knowledge Bases。retrieve をツールとして設計する |
| [11-auth](11-auth/) | 認証・認可。Cognito / JWT / Runtime の authorizer |
| [12-streaming](12-streaming/) | Next.js。JWT 検証つき Route Handler とストリーミング表示 |
| [13-evaluation](13-evaluation/) | 評価。判定関数・ケース設計・改善ループ |
| [14-prompt-injection](14-prompt-injection/) | プロンプトインジェクション耐性と多層防御 |
| [15-mcp](15-mcp/) | MCP サーバ。ツールのプロトコル分離 |
| [16-prompt-caching](16-prompt-caching/) | プロンプトキャッシュ。前方一致とコスト実測 |
| [17-guardrails](17-guardrails/) | Bedrock Guardrails。マネージド層の内容フィルタ |
| [18-hitl](18-hitl/) | HITL。取り消せない操作への承認ゲート |
| [19-structured-output](19-structured-output/) | 構造化出力。テキストパースの撤去 |
| [99-appendix](99-appendix/) | 発展領域の入口（RAG / Memory / OTel / Gateway） |

Tier 分けと習得判定は [docs/learning-roadmap.md](docs/learning-roadmap.md) にあります。

## 順序と前提

- 00 → 06 は直列（03 で作ったツールを 06 でテストする依存がある）
- 08・09 は 03 まで終えていれば並行できる。10 は 01 まで終えていれば独立に進められる
- 11 は 9 の後、12 は 11 の後
- 13 → 14 は連続で（14 の耐性 eval は 13 のハーネスに載る）。15〜19 は独立
- すべての章の合格判定は AWS 認証なしで通せる。実機確認（要 AWS）は
  [docs/aws-checklist.md](docs/aws-checklist.md) で後からまとめて回収できる

## 困ったら

`./scripts/check_env.sh` を実行して、環境の問題かコードの問題かを切り分けてください。
[docs/troubleshooting.md](docs/troubleshooting.md) には、このリポジトリの開発中に
実際に踏んだ問題だけが症状・原因・対処の順で載っています。
