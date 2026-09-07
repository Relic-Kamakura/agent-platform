# バージョン依存の値

教材の本文にはこの表の値を書かない。本文からは「versions.md を参照」の形で参照する。
モデルの世代交代やライブラリの更新で変わるのはこのファイルだけにする。

最終確認日: 2026-08-30

## モデル

| 項目 | 値 |
| --- | --- |
| 既定モデル ID | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| 接頭辞なしの ID | `anthropic.claude-haiku-4-5-20251001-v1:0` |
| コンテキストウィンドウ | 200K トークン |
| 最大出力 | 64K トークン |
| 最小キャッシュ長 | 4096 トークン |

東京リージョンでは地理接頭辞 `apac.` ではなく国別の `jp.` プロファイルのみ提供される。
実在する ID の一覧は `aws bedrock list-inference-profiles --region <リージョン>` で確認する。

## 単価（USD / 100万トークン）

| モデル | 入力 | 出力 |
| --- | --- | --- |
| Haiku 4.5 | 1 | 5 |
| Sonnet 系 | 3 | 15 |

リージョンと契約で変わる。バッチ推論の割引幅とプロビジョンドスループットの単価も同様。

## 埋め込みモデル

| 項目 | 値 |
| --- | --- |
| Titan Text Embeddings V2 の次元数 | 1024 / 512 / 256 |

## AgentCore Runtime の実行上限

| 項目 | 値 |
| --- | --- |
| 同期呼び出し | 15 分 |
| ストリーミング | 60 分 |
| 非同期ジョブ | 8 時間 |
| セッション | 既定 15 分、最長 8 時間 |
| ペイロード | 100 MB |
| セッション ID の最小長 | 33 文字 |

## AgentCore Runtime のクォータ（既定値）

| 項目 | 値 | 引き上げ |
| --- | --- | --- |
| データプレーン API のレート | 1,000 TPS | 可 |
| 新規セッション作成レート | 25 TPS | 可 |
| 同時アクティブセッション | 5,000 または 2,500 | 可 |

いずれもアカウント単位で、全エンドポイントが共有する（エンドポイントごとの上限ではない）。
データプレーン API は InvokeAgentRuntime を含む呼び出し系 API の合算。セッション作成レートは
コンテナと直接コードデプロイの両方に同じ値が適用される。同時アクティブセッションは
us-east-1 / us-west-2 が 5,000、他リージョンが 2,500。引き上げは Service Quotas から申請する。
出典: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/bedrock-agentcore-limits.html（2026-08-30 確認）

## AgentCore Runtime のセッション分離

セッションごとに専用の microVM が起動し、CPU・メモリ・ファイルシステムが分離され、
セッション終了時に microVM が破棄されてメモリがサニタイズされる。公式ドキュメントで確認済み（2026-08-30）。

- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html

## コールドスタート（このリポジトリでの実測値）

| Dockerfile の CMD | コールドスタート |
| --- | --- |
| `--no-sync` なし | 8 秒 |
| `--no-sync` あり | 4 秒 |

確認状況: 07-full-app のイメージで実測した値。環境依存で、ベースイメージや依存の量で変わる。

## 引用した実測値と目標値（AWS ブログ）

出典: https://aws.amazon.com/jp/blogs/news/ai-agents-in-enterprises-best-practices-with-amazon-bedrock-agentcore/（2026-08-30 確認）

現在日付を取得する手段の比較（第5章 5.2.3 から参照）。

| 項目 | ツールとして公開 | 属性として渡す |
| --- | --- | --- |
| LLM 呼び出し回数 | 4 回 | 3 回 |
| 合計トークン数 | 約 8,500 | 約 6,200 |
| レイテンシー | 12 秒 | 9 秒 |

評価指標の目標値の例（第9章 9.2.1 から参照）。

| 指標 | 目標値 |
| --- | --- |
| ツール選択精度 | 95% |
| パラメータ抽出精度 | 98% |
| 拒否精度 | 100% |
| レイテンシー | P50 2 秒未満、P95 5 秒未満 |
| クエリあたりのトークン数 | 平均 5,000 未満 |

## ライブラリ

| 項目 | 値 |
| --- | --- |
| Python | 3.12 以上 |
| strands-agents | 1.53.0 |
| aws-cdk-lib | 2.264.0 |

`strands-agents` には `max_turns` 相当の引数が無い（1.52.0 で確認）。
