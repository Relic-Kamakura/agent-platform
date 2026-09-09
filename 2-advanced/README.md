# 第2部 応用編

基礎編（`1-basic/`）で作ったエージェントを、実務の品質へ仕上げる部です。
RAG、評価、インジェクション耐性、MCP、キャッシュ、内容フィルタ、承認ゲート、構造化出力の 8 章に加え、それらを組み合わせて検索基盤を作る第16章があります。
どの順で進めてもかまいません（root README の「順序と前提」参照）。
デプロイ、IaC、認証、フロントエンドは第3部 本番運用基盤（`3-production/`）にあります。

## 章の一覧

| 章 | 学べること |
| --- | --- |
| [08-knowledge-base](08-knowledge-base/) | RAG を手で作る |
| [09-evaluation](09-evaluation/) | 判定関数と改善ループ |
| [10-prompt-injection](10-prompt-injection/) | インジェクション耐性と多層防御 |
| [11-mcp](11-mcp/) | MCP サーバによる分離 |
| [12-prompt-caching](12-prompt-caching/) | プロンプトキャッシュとコスト実測 |
| [13-guardrails](13-guardrails/) | マネージド層の内容フィルタ |
| [14-hitl](14-hitl/) | 取り消せない操作の承認ゲート |
| [15-structured-output](15-structured-output/) | 構造化出力とパースの撤去 |
| [16-news-kb-mcp](16-news-kb-mcp/) | KB 取り込みと Gateway 検索基盤 |

## 第16章の位置づけ

第16章は、第8章（KB）、第11章（MCP）、第18章（CDK）、第19章（Cognito と JWT）で学んだ要素を 1 つの検索基盤に組み上げる章です。
AWS の更新情報 RSS を Knowledge Base へ取り込み、AgentCore Gateway 経由の MCP ツールとして Claude Code などから検索します。
取り込み（書き込み専任）と読み取り（読み取り専任）を S3 と KB だけでつなぐ疎結合の構成で、第3部を終えていなくても、前提の 4 章が済んでいれば進められます。
