# 第11章 認証と認可

この章を終えると、Cognito User Pool を CDK で自分で書き、AgentCore Runtime に inbound JWT authorizer を設定する形を説明できるようになります。
「誰がエージェントを呼べるか」をコードで定義する章です。

この章は独立した CDK プロジェクトです。最初に依存を入れてください。

```bash
cd 11-auth
npm ci
```

## 11.1 概要

### 11.1.1 認証と認可

認証（authentication）は「相手が誰か」を確かめることで、認可（authorization）は「その相手に何を許すか」を決めることです。
この章で作るのは、認証の仕組み（Cognito がユーザを確認してトークンを発行する）と、それに基づく認可の判定（有効なトークンを持つ呼び出しだけを Runtime に通す）の両方です。

エージェントは呼び出されるたびに Bedrock のトークン費用が発生します。
認可の無い API として公開すれば、誰でもそのコストを積み上げられてしまいます。

### 11.1.2 認証経路の全体像

このリポジトリの完成形の経路です。設計の原則は、AWS の認証情報をブラウザに置かないことです。

```
ブラウザ ── ①ログイン ──→ Cognito（ID/アクセストークンを発行）
   │
   ├ ②アクセストークン付きで POST /api/invoke
   ▼
Next.js Route Handler（サーバ側）── ③JWT を検証 ── ④AWS SDK で InvokeAgentRuntime
   ▼
AgentCore Runtime ── ⑤Runtime 側でも JWT authorizer が検証
```

③と⑤で二重に検証しているのは役割が違うからです。
③はアプリの入口での検証、⑤は Route Handler を経由せずに Runtime を直接呼び出す経路を塞ぐ、基盤側の検証です。
この章が扱うのは①の Cognito と⑤の JWT authorizer です。

### 11.1.3 Cognito と JWT の仕組み

Cognito User Pool はユーザディレクトリ + トークン発行者です。ログインに成功すると 3 種のトークンが返ります。

- ID トークン — ユーザ属性（メール等）を含む。画面表示用
- アクセストークン — API 呼び出しの認可に使う。この章で使うのはこれ
- リフレッシュトークン — 上の 2 つを再発行するための長寿命トークン

検証側は署名を確かめる必要があります。
User Pool は公開鍵一覧（JWKS）を既知の URL で公開しており、その場所を検証側に知らせる URL が discovery URL です。

```
https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/openid-configuration
```

検証側はこの URL から JWKS の場所を知り、公開鍵で署名を検証し、`iss`（発行者）と `aud` / `client_id`（宛先）が想定どおりかを確かめます。
これは OpenID Connect の標準的な仕組みで、Cognito 固有ではありません。

## 11.2 実装のポイント

### 11.2.1 Runtime 側の JWT authorizer

AgentCore Runtime には JWT authorizer を設定できます（`CfnRuntime` の `authorizerConfiguration.customJwtAuthorizer`。型定義で確認済み）。
設定の形はこうなります。

```ts
new agentcore.CfnRuntime(this, 'AgentRuntime', {
  // ...（第9章で書いた Runtime の定義）
  authorizerConfiguration: {
    customJwtAuthorizer: {
      // 11.1.3 の URL。ここから鍵を取って検証する
      discoveryUrl: authStack.discoveryUrl,
      // 許可する App Client ID の一覧。他の Client のトークンは弾く
      allowedClients: [authStack.clientId],
    },
  },
});
```

これを設定すると、`InvokeAgentRuntime` の呼び出しに有効な JWT が必要になります。
第9章の Runtime スタックはこの 2 値を props で受け取れるようにしてあり、この章で作る AuthStack の公開プロパティ（`discoveryUrl` / `clientId`）をそのまま渡せば配線が完成します。

### 11.2.2 この章で書く AuthStack

Cognito 側は L2 が揃っているので、`cognito.UserPool` と `pool.addClient()` で書けます。
判断が要るのは設定値のほうです。

`selfSignUpEnabled: false` にして、ユーザは管理者が作る形にします。
true にすると誰でもアカウントを作れてしまい、認可を付けた意味が消えます。

`authFlows: { userPassword: true }` は 11.4 で CLI からログインするためのもので、
本番の Web アプリでは SRP や Hosted UI を検討します。
`removalPolicy: DESTROY` はひな形なので消しやすさ優先です。本番では RETAIN にします。

### 11.2.3 エージェントの権限と、呼び出したユーザの権限

JWT を検証すれば誰が呼んだかは分かります。
一方でエージェント自身は、第9章で作った実行ロール 1 つで動きます。
一般社員が呼んでも部長が呼んでも、ツールが使う権限は同じです。
ここを詰めないと、権限の弱いユーザがエージェント越しに自分では触れないデータへ届きます。
9.2.2 の信頼ポリシーで防いだ confused deputy と、形は同じです。

対処は 2 段構えになります。
まず実行ロールの権限を、一番弱いユーザに許してよい範囲まで落とします。
ロールが持っていない権限は、誰がどう頼んでも引き出せません。
それで足りないなら、呼び出したユーザの識別子をツールまで引き回して、ツールの中で絞ります。

RAG を足したときに、この差が問題になります（第10章）。
Knowledge Base は取り込んだ文書を全部インデックスするので、retrieve は既定で全社の文書を横断して返します。
人事評価のメモも、聞かれれば断片が出ます。
検索結果を閲覧権限でフィルタしない限り、入口に認証を掛けても中身は制限されません。

Bedrock Knowledge Bases にはメタデータによる絞り込みがあるので、取り込み時に文書へ閲覧範囲を持たせ、Retrieve のフィルタに JWT から取り出した所属を渡す形になります。
KB を作った後では取り込み直しになるので、決めるのは先です。

## 11.3 【ハンズオン】AuthStack を書く

編集するのは `lib/auth-stack.ts` の 1 ファイルだけです。骨組みをコピーして作ります。

```bash
mkdir -p lib && cp exercises/auth-stack.ts lib/auth-stack.ts
```

### 11.3.1 TODO を 4 つ埋める

`lib/auth-stack.ts` を開いてください。クラスの枠と公開プロパティは書いてあり、TODO が 4 つ残っています。

1. `cognito.UserPool` を作る（設定値は 11.2.2 のとおり）
2. `pool.addClient()` で App Client を作る
3. `discoveryUrl` と `clientId` を組み立てる。discoveryUrl は `pool.userPoolProviderUrl` に `/.well-known/openid-configuration` を連結する
4. `CfnOutput` で UserPoolId / ClientId / DiscoveryUrl を出力する。11.4 のコマンドで使う値です

エントリポイント `bin/app.ts` は用意してあり（編集不要）、このファイルを `AgentPlatformAuthStack` として読み込みます。

### 11.3.2 synth で確認する

実装できたら TODO コメントを消し、CloudFormation テンプレートに変換してみます。

```bash
npx cdk synth AgentPlatformAuthStack | grep -E 'Cognito::UserPool|USER_PASSWORD'
```

`AWS::Cognito::UserPool` と `AWS::Cognito::UserPoolClient`、認証フローの `USER_PASSWORD_AUTH` が出るはずです。

### 11.3.3 合格判定

```bash
./verify/verify.sh
```

型チェックと synth の結果から、UserPool / App Client / discovery URL の形 / CfnOutput を検査します。

<details>
<summary>解答例</summary>

```ts
    const pool = new cognito.UserPool(this, 'UserPool', {
      // 社内利用の想定。ユーザは管理者が作る
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      // ひな形なので消しやすさ優先。本番では RETAIN に変えること
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const client = pool.addClient('AppClient', {
      // USER_PASSWORD_AUTH: ハンズオンで CLI からログインするため。
      // 本番の Web アプリでは SRP / Hosted UI を検討する
      authFlows: { userPassword: true },
      generateSecret: false,
    });

    // OIDC の discovery URL。JWT 検証側はここから JWKS の場所を知る
    this.discoveryUrl = `${pool.userPoolProviderUrl}/.well-known/openid-configuration`;
    this.clientId = client.userPoolClientId;

    new CfnOutput(this, 'UserPoolId', { value: pool.userPoolId });
    new CfnOutput(this, 'ClientId', { value: this.clientId });
    new CfnOutput(this, 'DiscoveryUrl', { value: this.discoveryUrl });
```

全文は `solutions/auth-stack.ts` にあります。

</details>

## 11.4 【ハンズオン】デプロイしてトークンを取得する

作った AuthStack をデプロイし、テストユーザのトークンで呼び出しを確かめます。

```bash
npx cdk deploy AgentPlatformAuthStack
```

Outputs に UserPoolId / ClientId / DiscoveryUrl が表示されるはずです。以降のコマンドの `<UserPoolId>` / `<ClientId>` をこの値で置き換えてください。

```bash
aws cognito-idp admin-create-user --user-pool-id <UserPoolId> \
  --username test@example.com --temporary-password 'TempPass123!' \
  --message-action SUPPRESS
```

```bash
aws cognito-idp admin-set-user-password --user-pool-id <UserPoolId> \
  --username test@example.com --password 'TestPass123!' --permanent
```

```bash
aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH \
  --client-id <ClientId> \
  --auth-parameters USERNAME=test@example.com,PASSWORD='TestPass123!' \
  --query 'AuthenticationResult.AccessToken' --output text
```

`eyJ` で始まる長い文字列（JWT）が出るはずです。
第9章の Runtime に 11.2.1 の authorizer を設定してデプロイ済みなら、このトークンを Bearer として `InvokeAgentRuntime` を呼べること、トークン無しだと拒否されることまで確認できます。

## 11.5 まとめ

トークンの発行は Cognito が担い、検証は discovery URL から公開鍵を取れる側なら誰でも行えます。
発行と検証を分離しているのが OpenID Connect の設計で、この分離があるから、アプリの入口（Route Handler）と基盤（Runtime の JWT authorizer）の二重の検証を同じ User Pool から配線できます。
次の第12章では、この経路の残り、③の JWT 検証を行う Route Handler を自分で書きます。

## 次の章

[第12章 フロントエンドとストリーミング](../12-streaming/)
