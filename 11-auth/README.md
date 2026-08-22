# 第11章 認証と認可 — Cognito / JWT

この章を終えると、Cognito User Pool を CDK で自分で書き、AgentCore Runtime に
inbound JWT authorizer を配線できるようになります。「誰がエージェントを呼べるか」を
コードで定義する章です。

実装は第9章と同じ `09-infra-as-code/` に追加します。

## 11.1 概要

### 11.1.1 認証と認可

認証（authentication）は「相手が誰か」を確かめることで、認可（authorization）は
「その相手に何を許すか」を決めることです。この章で作るのは、認証の仕組み
（Cognito がユーザを確認してトークンを発行する）と、それに基づく認可の判定
（有効なトークンを持つ呼び出しだけを Runtime に通す）の両方です。

エージェントは呼び出されるたびに Bedrock のトークン費用が発生します。
認可の無い API として公開すれば、誰でもそのコストを積み上げられてしまいます。

### 11.1.2 認証経路の全体像

このリポジトリの完成形の経路です。AWS の認証情報をブラウザに出さないことが柱です。

```
ブラウザ ── ①ログイン ──→ Cognito（ID/アクセストークンを発行）
   │
   ├ ②アクセストークン付きで POST /api/invoke
   ▼
Next.js Route Handler（サーバ側）── ③JWT を検証 ── ④AWS SDK で InvokeAgentRuntime
   ▼
AgentCore Runtime ── ⑤Runtime 側でも JWT authorizer が検証（この章で配線）
```

③と⑤で二重に検証しているのは役割が違うからです。③はアプリの入口の門番、
⑤は「Route Handler を経由しない直叩き」を防ぐ基盤側の門番です。

### 11.1.3 Cognito と JWT の仕組み

Cognito User Pool はユーザディレクトリ + トークン発行者です。ログインに成功すると
3 種のトークンが返ります。

- **ID トークン** — ユーザ属性（メール等）を含む。画面表示用
- **アクセストークン** — API 呼び出しの認可に使う。今回の主役
- **リフレッシュトークン** — 上 2 つを再発行するための長寿命トークン

検証側は署名を確かめる必要があります。User Pool は公開鍵一覧（JWKS）を
既知の URL で公開しており、その入口が **discovery URL** です。

```
https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/openid-configuration
```

検証側はこの URL から JWKS の場所を知り、公開鍵で署名を検証し、
`iss`（発行者）と `aud` / `client_id`（宛先）が想定どおりかを確かめます。
これは OpenID Connect の標準的な仕組みで、Cognito 固有ではありません。

## 11.2 実装のポイント — inbound JWT authorizer

Runtime には JWT authorizer を設定できます（`CfnRuntime` の
`authorizerConfiguration.customJwtAuthorizer`。型定義で確認済み）。

- `discoveryUrl`（必須） — 11.1.3 の URL。ここから鍵を取って検証する
- `allowedClients` — 許可する App Client ID の一覧
- `allowedAudience` — aud クレームの許可リスト

これを設定すると、`InvokeAgentRuntime` の呼び出しに有効な JWT が必要になります。
第9章で書いた `AgentRuntimeStack` は既にこの口（`jwtDiscoveryUrl` /
`jwtAllowedClients` props）を持っています。この章では Cognito 側を作って配線します。

## 11.3 【ハンズオン】AuthStack を書いて配線する

### 11.3.1 AuthStack を書く

`09-infra-as-code/lib/auth-stack.ts` を新規作成してください。要件:

1. `AuthStack` クラス。`cognito.UserPool` を 1 つ作る
   - `selfSignUpEnabled: false`（社内利用。管理者がユーザを作る）
   - `signInAliases: { email: true }`
   - パスワードポリシーは CDK の既定でよい
   - ひな形なので `removalPolicy: DESTROY`（理由コメントを書く）
2. `pool.addClient()` で App Client を 1 つ作る
   - `authFlows: { userPassword: true }`（ハンズオンで CLI からログインするため）
   - `generateSecret: false`
3. 公開プロパティとして `discoveryUrl: string` と `clientId: string` を持たせる
   - discoveryUrl は `pool.userPoolProviderUrl` に
     `/.well-known/openid-configuration` を連結して組み立てる
4. `CfnOutput` で UserPoolId / ClientId / DiscoveryUrl を出力する

### 11.3.2 bin/app.ts に配線する

`AuthStack` を生成し、`AgentRuntimeStack` に `jwtDiscoveryUrl` と
`jwtAllowedClients: [authStack.clientId]` を渡してください。
スタック名は `AgentPlatformAuthStack` とします。

### 11.3.3 synth で確認する

```bash
cd 09-infra-as-code
CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth AgentPlatformAuthStack | grep -E 'UserPool|Client' | head
```

`AWS::Cognito::UserPool` と `AWS::Cognito::UserPoolClient` が出るはずです。
Runtime 側への配線も確認します。

```bash
CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth AgentPlatformRuntimeStack | grep -A3 CustomJWTAuthorizer
```

`DiscoveryUrl` に Cognito の URL（トークン参照）が入っていれば配線成功です。

### 11.3.4 合格判定

```bash
./11-auth/verify/verify.sh
```

詰まったら `solutions/` を見てください。

## 11.4 【ハンズオン】トークンを取得して呼び出す

デプロイし、テストユーザを作り、実際のトークンで呼び出します。

```bash
cd 09-infra-as-code && npx cdk deploy AgentPlatformAuthStack AgentPlatformRuntimeStack
```

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

取得したアクセストークンを Bearer として `InvokeAgentRuntime` を呼び、
トークン無しだと拒否されることも確認してください。

## 11.5 まとめ

認証は Cognito に任せ、認可の判定は discovery URL を知っている側なら誰でもできる——
この分離が OpenID Connect の設計で、だからアプリの入口（Route Handler）と基盤
（Runtime の JWT authorizer）の **二重の門番** を同じ User Pool から配線できます。
次の第12章では、この経路のブラウザ側、つまり③の JWT 検証を持つ Route Handler を
自分で書きます。

## 次の章

[第12章 フロントエンドとストリーミング](../12-streaming/)
