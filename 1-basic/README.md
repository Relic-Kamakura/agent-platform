# 第1部 基礎編

エージェント開発のコアを、競合リサーチエージェントを題材に一本道で実装する部です。
第0〜7章を番号順に進めると、モデル呼び出しからエージェントループ、ツール設計、コスト制御、マルチエージェント、テストまでを自分の手で書き、最後に完成形の本体（`07-full-app/`）を通読します。

## 章の一覧

| 章 | 学べること |
| --- | --- |
| [00-dev-environment](00-dev-environment/) | uv / Docker / AWS CLI の環境構築 |
| [01-invoke-bedrock](01-invoke-bedrock/) | Bedrock でモデルを呼ぶ |
| [02-agent-loop](02-agent-loop/) | エージェントループと ReAct |
| [03-tool-design](03-tool-design/) | ツール設計とエラー設計 |
| [04-cost-control](04-cost-control/) | hooks による上限とトークン計測 |
| [05-multi-agent](05-multi-agent/) | 役割分割とモデルの使い分け |
| [06-agent-testing](06-agent-testing/) | LLM を呼ばないテスト |
| [07-full-app](07-full-app/) | 完成形の通読 |

## 進め方と前提

第0章で AWS 接続とツールチェーンを整えたら、あとは番号順です。
各章は独立した uv プロジェクトで、章の冒頭に書いてある `uv sync` だけでその章の環境が完結します。
この部を終えると、第2部（エージェントの中身を仕上げるテーマ別の章）と第3部（本番運用基盤）はどちらからでも進められます。
