# 付録 — 発展領域の入口

案件要件が出たときに学ぶ領域（ロードマップ Tier 3）。章としての演習はまだ無く、
何を学ぶ領域か・どこから入るか・本編との接続だけをまとめておく。
着手する案件が決まったら、この付録を本編と同じ型の章に格上げする。

## A. RAG と Bedrock Knowledge Bases

社内文書やナレッジを検索してモデルの回答に組み込む技術。本編の web_search が
「外部の公開情報」を引くのに対し、RAG は「自分たちのデータ」を引く。
Bedrock Knowledge Bases は、S3 のドキュメント取り込み・ベクトル化・検索 API までを
マネージドで提供する AWS 版の RAG 基盤。

- 本編との接続: 第3章のツール設計がそのまま使える。Knowledge Bases の Retrieve API を
  ツールとして包めば、このエージェントは社内文書も引けるようになる
- 入口: Bedrock Knowledge Bases の開発者ガイド。最小構成は S3 + KB + Retrieve ツール
- 注意: 本編の題材（Web 検索型）と混ぜず、別モジュールとして作ること

## B. AgentCore Memory — マルチターン会話

本編のエージェントはワンショット（1 依頼 1 応答）。会話の続きや利用者ごとの
文脈を保持するには記憶の設計が要る。AgentCore Memory は短期（セッション内）と
長期（セッション横断）の記憶をマネージドで提供する。

- 本編との接続: `InvokeAgentRuntime` の runtimeSessionId（第8章）がセッションの単位。
  東京リージョン対応済み（第0章の対応表）
- 入口: AgentCore Memory の開発者ガイドと Strands の session_manager

## C. オブザーバビリティ — OpenTelemetry / AgentCore Observability

本編の構造化ログ（第4章）はプロセス内の記録。複数エージェント・複数サービスに
またがる 1 リクエストを追うには分散トレースが要る。AgentCore Observability は
OTel 形式のトレースを CloudWatch で可視化する。

- 本編との接続: `aws-opentelemetry-distro` を Dockerfile に足し、
  `opentelemetry-instrument` 経由で起動する形が公式の型
- トレードオフ: イメージサイズとコールドスタート（第8章で計測した 4 秒）への影響を
  実測してから本番採用を判断する

## D. AgentCore Gateway — 既存 API の MCP 化

社内の既存 REST API 群を、コードを書かずに MCP ツールとして公開するマネージド機能。
第14章で自作した MCP サーバの「運用をマネージドに寄せた版」と考えるとよい。

- 本編との接続: 第14章の発展。自作 MCP サーバとの使い分けは
  「変換ロジックが要るなら自作、素直な API 公開なら Gateway」
- 入口: AgentCore Gateway の開発者ガイド（東京リージョン対応済み）
