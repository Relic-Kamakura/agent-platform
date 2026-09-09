# 第3部 本番運用基盤

作ったエージェントを外へ届ける側の部です。エージェントの中身（第1・2部）とは独立した主題として分けてあります。
コンテナデプロイ、IaC、認証、フロントエンドの 4 章と付録で、担当がインフラや配信に回る人向けのトラックです。

## 章の一覧

| 章 | 学べること |
| --- | --- |
| [17-agentcore-deploy](17-agentcore-deploy/) | コンテナの要求条件とデプロイ |
| [18-infra-as-code](18-infra-as-code/) | CDK と IAM ロール設計 |
| [19-auth](19-auth/) | Cognito と JWT による認可 |
| [20-streaming](20-streaming/) | Next.js とストリーミング表示 |
| [99-appendix](99-appendix/) | 発展領域の入口と用語集 |

## 進め方

各章は独立したプロジェクトで、章の冒頭のセットアップだけで始められます。
デプロイ対象は第1部の本体 `1-basic/07-full-app` で、`./scripts/deploy.sh` が ECR の作成 → イメージ push → Runtime の作成の順序を守ります（L1 の CfnRuntime と自前の ECR を使うこの構成では、Runtime の作成時点でイメージが ECR に無いと失敗するためです）。
