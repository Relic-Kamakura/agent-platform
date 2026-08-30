# 付録 発展領域の入口

案件要件が出たときに学ぶ領域（ロードマップ Tier 3）です。章としての演習はまだ無く、
何を学ぶ領域か、どこから入るか、本編との接続だけをまとめています。
着手する案件が決まったら、この付録を本編と同じ構成（README + verify + solutions）の
章として作り直します。

## A. RAG と Bedrock Knowledge Bases

社内文書やナレッジを検索してモデルの回答に組み込む技術です。本編の web_search が
外部の公開情報を引くのに対し、RAG は自分たちのデータを引きます。
Bedrock Knowledge Bases は、S3 のドキュメント取り込み、ベクトル化、検索 API までを
マネージドで提供する AWS 版の RAG 基盤です。
仕組みの基礎と最小の retrieve ツールは [第10章](../10-knowledge-base/) が本編で扱います。
この節は第10章の先、KB + S3 + ベクトル検索を組み合わせた本格構成に
進むときの入口です。

本編との接続は第3章のツール設計で、Retrieve API をツールとして包めば
このエージェントは社内文書も引けるようになります（第10章で実装します）。
入口は Bedrock Knowledge Bases の開発者ガイドです。
本編の題材（Web 検索型）とは混ぜず、別モジュールとして作ってください。

## B. AgentCore Memory（マルチターン会話）

本編のエージェントはワンショット（1 依頼 1 応答）です。会話の続きや利用者ごとの
前提を保持するには記憶の設計が要ります。AgentCore Memory は短期（セッション内）と
長期（セッション横断）の記憶をマネージドで提供します。

セッションの単位は `InvokeAgentRuntime` の runtimeSessionId（第8章）で、
東京リージョンにも対応済みです。
入口は AgentCore Memory の開発者ガイドと Strands の session_manager です。

## C. オブザーバビリティ（OpenTelemetry / AgentCore Observability）

本編の構造化ログ（第4章）はプロセス内の記録です。複数エージェントや複数サービスに
またがる 1 リクエストを追うには分散トレースが要ります。AgentCore Observability は
OTel 形式のトレースを CloudWatch で可視化します。

導入は `aws-opentelemetry-distro` を Dockerfile に足し、
`opentelemetry-instrument` 経由で起動します（公式ドキュメントの手順）。
イメージサイズとコールドスタート（第8章で計測した 4 秒）への影響を実測してから、
本番採用を判断してください。

## D. AgentCore Gateway（既存 API の MCP 化）

社内の既存 REST API 群を、コードを書かずに MCP ツールとして公開するマネージド機能です。
第15章で自作した MCP サーバと同じ役割を、サーバの実装と運用を AWS 側に任せる形で
提供します。

第15章の発展にあたります。自作 MCP サーバとの使い分けは、変換ロジックが要るなら自作、
既存 API をそのままツールとして公開するだけなら Gateway です。
入口は AgentCore Gateway の開発者ガイド（東京リージョン対応済み）です。

## E. 用語集

本編では扱いませんが、案件の要件定義や資格の出題範囲で名前が出るものです。
何をするものかと、どういう要件のときに候補になるかだけ載せます。

| 用語 | 何をするものか | 候補になる場面 |
| --- | --- | --- |
| Amazon Kendra | 権限フィルタ付き全社検索 | 社内システムの横断検索 |
| SageMaker JumpStart | 公開モデルの自前ホスト | Bedrock に無いモデル |
| AWS Artifact | AWS の統制文書を取る | 顧客の監査対応 |
| Amazon DataZone | データのカタログと権限 | 入力データの由来説明 |
| SageMaker Model Monitor | 推論のドリフト検知 | 自前学習モデルの運用 |

Kendra は SharePoint や Salesforce のコネクタを持ち、利用者ごとに見える範囲を変えられます。
文書を S3 に集められるなら Knowledge Bases（第10章）で足りることが多いです。
JumpStart を使うと、推論エンドポイントを常時起動する費用と運用を引き受けることになります。
AWS Artifact で取れるのは SOC や ISO の報告書で、セキュリティチェックシートの証跡に使います。
DataZone のデータリネージはデータの出どころと加工経路の追跡で、
RAG の取り込み元の統制（第10章）とつながる領域です。
Model Monitor は学習時からのずれを見るもので、基盤モデルを API で呼ぶ構成では出番がありません。
その役目は第13章の evals と第4章のログが担います。
