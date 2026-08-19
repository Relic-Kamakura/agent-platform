# AWS 接続後にやることリスト

各章の合格判定（verify）はすべてオフラインで通せる設計だが、実際にモデルを呼ぶ・
デプロイする確認は AWS 認証が要る。認証が使える状態になったら、上から順に消化する。

前提: `aws sts get-caller-identity` が通ること。だめなら `aws login`（または `aws sso login`）。

| # | 章 | やること | コマンド / 節 |
| --- | --- | --- | --- |
| 1 | 00 | check_env.sh のセクション 3〜5 を全 OK にする | `./scripts/check_env.sh` |
| 2 | 01 | 推論プロファイル一覧で `.env` のモデル ID を確定 | README 1.5.1 |
| 3 | 01 | 生 Converse を 1 回呼ぶ | `uv run 01_converse.py`（章内） |
| 4 | 02 | 自作エージェントを実行し cycle_count を観察 | README 2.6 |
| 5 | 07 | ローカル起動で実プロンプトの往復を 1 回通す | README 7.1 + curl /invocations |
| 6 | 08 | デプロイして InvokeAgentRuntime で 1 回呼ぶ | `./scripts/deploy.sh` → README 8.6 |
| 7 | 10 | Cognito をデプロイし、トークン取得 → JWT 付き呼び出し | README 10.5 |
| 8 | 11 | フロントからの一気通貫（AUTH_BYPASS なし） | README 11.5 |
| 9 | 12 | eval を実行し、改善ループを一周 | README 12.5 |
| 10 | 13 | インジェクション耐性 eval で「従わない」ことを確認 | README 13.4 |
| 11 | 15 | プロンプトキャッシュの前後でコストを実測比較 | README 15.3 |
| 12 | 16 | Guardrail をデプロイして発動を確認 | README 16.4 |

6 を終えた時点で plan.md の Phase 2 の動作確認、7〜8 で Phase 3〜4、9〜10 で Phase 5 の
動作確認がそれぞれ完了する。終わったら plan.md のチェックを更新すること。
