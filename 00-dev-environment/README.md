# 第0章 開発環境について

この章ではハンズオンで使用する開発環境について解説します。
終えると、エージェント本体のテスト 38 件が通り、`./scripts/check_env.sh` で
環境の問題かコードの問題かを自分で切り分けられる状態になります。

## 0.1 概要

本教材は Python 製のエージェント本体（第1〜7章）と TypeScript 製の CDK（第9章）の
両方を扱うため、2 つのツールチェーンを先に揃えます。

- **uv** — Python の環境・依存管理する。venv の activate は不要
- **AWS CLI** — モデル一覧の確認とデプロイに使います。この章の時点では未認証で構いません。Sandboxを申請して使用してください。
- **Node.js / npm** — CDK（第9章）用

## 0.2 【ハンズオン】環境を構築する

### 0.2.1 ツールを導入する

Docker Desktop は公式サイトから入れてください。

```bash
brew install uv node awscli jq
```

### 0.2.2 エージェント本体のテストを通す

```bash
cd 07-full-app
uv sync
```

```bash
uv run pytest -q
```

`38 passed` と出るはずです。botocore の例外で落ちたら
`docs/troubleshooting.md` の先頭項目を読んでください。開発中に同じ現象を踏んでいます。

### 0.2.3 CDK の依存を入れる

```bash
cd ../09-infra-as-code
npm ci
```

```bash
npx tsc --noEmit
```

何も表示されなければ型チェック成功です。

### 0.2.4 環境チェックを流す

```bash
cd ..
./scripts/check_env.sh
```

## 0.3 合格条件

- pytest 38 件パス
- check_env.sh のセクション 1（コマンド）と 2（ARM64 ビルド）が全 OK
- セクション 3〜5 は AWS 認証後に確認すればよい

## 0.4 まとめ

ここで通した **pytest 38 件と check_env.sh** が、以降の全章で「環境の問題か
コードの問題か」を切り分ける基準線になります。この先で謎の失敗に当たったら、
コードを疑う前に `./scripts/check_env.sh` に戻ってください。
環境ができたら第1章へ進み、Bedrock を生で呼びます。

## 次の章

[第1章 Bedrock で Claude を呼び出す](../01-invoke-bedrock/)
