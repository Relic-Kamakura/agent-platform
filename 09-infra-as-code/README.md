# 第9章 基盤をコードで定義する

CDK (TypeScript) の本体であり、IaC を学ぶ章です。
終えると、L2 コンストラクタが無い新しめのサービスを L1 で書け、IAM 実行ロールの信頼ポリシーに何を書くべきか、なぜスタックを分けるのかを説明できるようになります。

依存を先に入れてください。

```bash
cd 09-infra-as-code
npm ci
```

## 9.1 概要

### 9.1.1 CDK とは

インフラを TypeScript のコードとして定義し、CloudFormation テンプレートに変換してデプロイする IaC ツールです。
コンソールの手作業と違い、何を作るかがコードレビューと差分確認（`npx cdk diff`）の対象になり、同じ構成を何度でも再現できます。

```mermaid
graph LR
    TS["lib/*.ts<br/>(TypeScript)"] -->|cdk synth| CF["CloudFormation<br/>テンプレート"] -->|cdk deploy| R[AWS リソース]
```

コンストラクタには階層があります。

- **L2**（`ecr.Repository` など） — 良い既定値とヘルパー付きの高水準 API
- **L1**（`Cfn` 始まり） — CloudFormation リソースと 1 対 1。全プロパティを自分で書く

### 9.1.2 L2 が無いサービスの書き方

AgentCore のような新しいサービスには L2 がまだありません。
これは開発中に一度間違えた点です。
「stable な L2 Runtime がある」と書いた Web 記事を信じて設計し、実装段階で `node_modules` の型定義を開いたら存在しませんでした。
aws-cdk-lib 2.264.0 の aws-bedrockagentcore に入っているのは L1 だけです。

この失敗から持ち帰るべきは確認方法です。
Web 記事の記述より、手元の `node_modules` にある型定義を信頼してください。

```bash
ls 09-infra-as-code/node_modules/aws-cdk-lib/aws-bedrockagentcore/lib/
```

`lib/agent-runtime-stack.ts` は `CfnRuntime` を直接使っています。
L1 は全プロパティを自分で書く手間がかかる代わり、CloudFormation リファレンスがそのまま読めるようになる副産物があります。

## 9.2 実装のポイント

### 9.2.1 スタックを 2 つに分けた理由

AgentCore Runtime は、作成時点で ECR にイメージが存在することを要求します。
ECR と Runtime を同じスタックに入れると、CloudFormation は「空のリポジトリを参照する Runtime」を作ろうとして失敗します。

一般化すると、CloudFormation が管理するのはリソースの存在であって、「イメージが push 済みか」という状態ではないからです。
リソースが IaC の管理外の状態に依存するとき、IaC 単体では順序を保証できません。
AgentCore に限らず繰り返し出会う問題です。

このリポジトリの解き方:

1. スタックを EcrStack と AgentRuntimeStack に分割する
2. `scripts/deploy.sh` が「ECR デプロイ → イメージ push → Runtime デプロイ」を強制する
3. `cdk deploy --all` の直接実行は禁止（CLAUDE.md の禁止事項）

### 9.2.2 IAM 実行ロールの信頼ポリシー

`resolveExecutionRole()` が Runtime の実行ロールを定義しています。
読みどころは信頼ポリシーです。

`bedrock-agentcore.amazonaws.com` からの AssumeRole を、`aws:SourceAccount` と `aws:SourceArn` の条件で自アカウント起源に限定しています。
条件が無いと、他人の AWS アカウントの AgentCore があなたのロールを引き受けられる余地が生まれます（confused deputy 問題）。
セキュリティレビューで必ず指摘される類のもので、最初から書く癖をつけてください。

権限は 3 つに絞ってあります。

- ECR からのイメージ pull
- Bedrock の InvokeModel / InvokeModelWithResponseStream
- CloudWatch Logs への書き込み

ロールを自分で作れない組織向けに、context で既存ロール ARN を渡すと新規作成をスキップする分岐も入れてあります。

### 9.2.3 context による環境差分の注入

リージョン、モデル ID、ロール ARN はコードに書かず、`cdk.json` の context に既定値を置いて `-c` で上書きします。
context を読むのは `lib/config.ts` の `loadConfig()` だけ。
Python 側の「config.py だけが環境変数を読む」と同じ規約です。

```bash
npx cdk deploy -c region=us-east-1 -c imageTag=v1.2.0
```

`cdk synth` はテンプレート生成だけでデプロイはしないので、デプロイ前に「この変更で何が作られるか」を確認できます。

## 9.3 【ハンズオン】context 経由で Runtime の環境変数を追加する

エージェントの `LOG_LEVEL` を CDK context から Runtime に注入できるようにします。
この章のディレクトリは動く CDK コードの本体でもあるため、骨組みのコピーではなく `lib/config.ts` と `cdk.json` を直接編集します。

### 9.3.1 config.ts に logLevel の読み取りを追加する

`lib/config.ts` の `loadConfig()` を開いてください。
`agentEnvironment` の組み立てに、context `logLevel` を読んで `LOG_LEVEL` に入れる処理を追加します。
`searchProvider` と同じ三項スプレッドのパターンで、未指定なら入れません。

### 9.3.2 cdk.json に既定値を置く

`cdk.json` の context に `"logLevel": "INFO"` を追加します。

### 9.3.3 型チェックと synth で確認する

```bash
cd 09-infra-as-code && npx tsc --noEmit
```

何も出力されなければ型は通っています。
synth への反映を確認します。

```bash
CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth AgentPlatformRuntimeStack \
  -c logLevel=DEBUG | grep LOG_LEVEL
```

`LOG_LEVEL: DEBUG` が出るはずです。

### 9.3.4 合格判定

```bash
cd .. && ./09-infra-as-code/verify/verify.sh
```

考えてみてください（記述・任意）。
`-c logLevel=DEBUG` と `07-full-app/.env` の `LOG_LEVEL=DEBUG` は、それぞれどの環境（ローカル実行とデプロイ済み Runtime）のログ設定に反映されるでしょうか。

<details>
<summary>解答例</summary>

`lib/config.ts` は `searchProvider` の処理の直後に追加します。

```typescript
    ...(app.node.tryGetContext('logLevel')
      ? { LOG_LEVEL: String(app.node.tryGetContext('logLevel')) }
      : {}),
```

`cdk.json` は context に 1 行追加します。

```json
    "logLevel": "INFO",
```

`loadConfig()` 以外の場所で `tryGetContext` を呼ばないでください。
設定の読み取り口を 1 箇所に保つのは Python 側（config.py）と同じ規約です。
「未指定なら入れない」三項スプレッドにより、context を消せば Runtime の環境変数からも消え、`.env` 側の既定値が生きます。
解説付きの全文は `solutions/README.md` にあります。

</details>

## 9.4 まとめ

CloudFormation が保証するのはリソースの存在までで、「イメージが push 済みか」のような管理外の状態は保証できません。
だからスタックを分け、順序は `scripts/deploy.sh` に持たせる。
**IaC の境界を見極めて、足りない保証を手順で補う**のがこの章の核心です。

## 次の章

[第10章 ナレッジベース](../10-knowledge-base/)
