# 第0章 開発環境について

終えると、本体のテスト 38 件と `scripts/check_env.sh` が通る環境が手元にでき、以降の章で失敗したときに環境の問題かコードの問題かを切り分けられる状態になります。

## 0.1 概要

本教材は Python 製のエージェント本体（第1〜7章）と TypeScript 製の CDK（第9章）の
両方を扱うため、2 つのツールチェーンを先に揃えます。

- uv は Python の実行環境と依存パッケージを管理します。venv の activate は不要です
- AWS CLI はモデル一覧の確認とデプロイに使います
- Node.js と npm は CDK（第9章）で使います

## 0.2 【ハンズオン】環境を構築する

### 0.2.1 ツールを導入する

Docker Desktop は公式サイトから入れてください。

```bash
brew install uv node awscli jq
```

### 0.2.2 AWS に接続する

Relic の Sandbox 環境を申請して使います。利用時の注意点を [AWS サンドボックス利用開始ガイド](https://relic-inc.esa.io/posts/9815) で先に確認してください。

```bash
aws login
```

ブラウザでサインインすると CLI に認証情報が保存されます。

```bash
aws sts get-caller-identity
```

Account と Arn が表示されるはずです。次にリージョンを確認します。

```bash
aws configure get region
```

何も出なければ `aws configure set region us-east-1` のように自分のリージョンを
設定します。リージョンによってモデル ID の地理接頭辞（`us.` / `apac.` / `eu.`）が
変わるため、第1章 1.3 の手順で呼べる ID を確認し、`07-full-app/.env` を合わせてください。

最後に AWS コンソールの Bedrock → Model access で Claude 系モデルを有効化します。
リージョンごとの設定です。未申請だと第1章で `AccessDeniedException` になります。

費用は、第1〜7章はモデル呼び出しの従量課金のみで固定費はありません。第1章は
1 回 0.1 円未満、第2章以降も 1 リクエスト数円〜数十円です。デプロイを伴う
第8章以降で AgentCore Runtime と ECR の課金が加わります。

### 0.2.3 エージェント本体のテストを通す

```bash
cd 07-full-app
uv sync
```

```bash
uv run pytest -q
```

`38 passed` と出るはずです。botocore の例外で失敗したら
`docs/troubleshooting.md` の先頭項目に原因と対処があります。

### 0.2.4 CDK の依存を入れる

```bash
cd ../09-infra-as-code
npm ci
```

```bash
npx tsc --noEmit
```

何も表示されなければ型チェック成功です。

### 0.2.5 環境チェックを実行する

```bash
cd ..
./scripts/check_env.sh
```

セクション 3〜5（AWS 認証、リージョン、モデルアクセス）まで全 OK が出るはずです。

## 0.3 合格条件

pytest 38 件が通り、check_env.sh の全セクションが OK になれば合格です。

## 0.4 まとめ

ここで通した pytest 38 件と check_env.sh が、以降の全章で環境の問題かコードの問題かを切り分ける基準線になります。この先で原因の分からない失敗に当たったら、コードを疑う前に `./scripts/check_env.sh` に戻ってください。
環境ができたら第1章へ進み、フレームワークを介さず SDK から Bedrock の
Converse API を直接呼び出します。

## 次の章

[第1章 Bedrock で Claude を呼び出す](../01-invoke-bedrock/)
