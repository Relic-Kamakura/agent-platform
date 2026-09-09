# 第0章 開発環境について

終えると、本体のテスト 41 件と `scripts/check_env.sh` が通る環境が手元にでき、どの章でも失敗したときに環境の問題かコードの問題かを切り分けられる状態になります。
uv、Docker、AWS CLI、Node.js がすでに揃っている人は、0.2.5 の環境チェックだけ実行して次へ進んでかまいません。

## 0.1 概要

この教材は Python 製のエージェント本体と TypeScript 製の CDK の両方を扱うため、2 つのツールチェーンを先に揃えます。

- uv は Python の実行環境と依存パッケージを管理します。venv の activate は不要です
- AWS CLI はモデル一覧の確認とデプロイに使います
- Node.js と npm は CDK で使います

## 0.2 ハンズオン: 開発環境を構築する

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

何も出なければ `aws configure set region us-east-1` のように自分のリージョンを設定します。
モデル ID の地理接頭辞（`us.` / `apac.` / `eu.` / 国別の `jp.`）はリージョンで変わるので、呼べる ID を一覧で確認します。

```bash
aws bedrock list-inference-profiles --region us-east-1 \
  --query 'inferenceProfileSummaries[].inferenceProfileId' | grep anthropic
```

一覧に無い ID を使うと `ValidationException` になります。`1-basic/07-full-app/.env` のモデル ID を一覧にある値に合わせてください。
最後に AWS コンソールの Bedrock → Model access で Claude 系モデルを有効化します。リージョンごとの設定で、未申請だと `AccessDeniedException` になります。

費用はモデル呼び出しの従量課金だけで、固定費はありません。1 リクエストあたり数円から数十円です。デプロイを伴う章では AgentCore Runtime と ECR の課金が加わります。

### 0.2.3 エージェント本体のテストを通す

本体 `1-basic/07-full-app` は競合リサーチエージェントの完成形です。テストはモデルを呼ばないので、AWS 接続に関係なく環境の確認に使えます。

```bash
cd 1-basic/07-full-app
uv sync
```

```bash
uv run pytest -q
```

`41 passed` と出るはずです。botocore の例外で失敗したら `docs/troubleshooting.md` の先頭項目に原因と対処があります。

### 0.2.4 CDK の依存を入れる

```bash
cd ../../3-production/18-infra-as-code
npm ci
```

```bash
npx tsc --noEmit
```

何も表示されなければ型チェック成功です。

### 0.2.5 環境チェックを実行する

```bash
cd ../..
./scripts/check_env.sh
```

セクション 3〜5（AWS 認証、リージョン、モデルアクセス）まで全 OK が出るはずです。

## 0.3 合格条件

pytest 41 件が通り、check_env.sh の全セクションが OK になれば合格です。

## 0.4 まとめ

ここで通した pytest 41 件と check_env.sh が、環境の問題かコードの問題かを切り分ける基準線になります。原因の分からない失敗に当たったら、コードを疑う前に `./scripts/check_env.sh` に戻ってください。

## 次の章

[第1章 Bedrock で Claude を呼び出す](../01-invoke-bedrock/)
