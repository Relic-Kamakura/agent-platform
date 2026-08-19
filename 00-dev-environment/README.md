# 第0章 開発環境を整える

この章を終えると `uv run pytest` が 38 件通り、`./scripts/check_env.sh` が
AWS 認証以外すべて OK になります。以降の章はこの状態が前提です。

## 0.1 使う道具

- **uv** — Python の環境・依存管理。`uv.lock` で全員のマシンに同じバージョンが入るため、
  「私の環境では動く」問題を排除できます。venv の activate は不要
- **Docker (buildx)** — デプロイ先の AgentCore Runtime は linux/arm64 イメージ限定（第8章）。
  Apple Silicon はネイティブ、Intel/Windows は QEMU が必要です
- **AWS CLI** — モデル一覧の確認とデプロイに使います。この章の時点では未認証で構いません
- **Node.js / npm** — CDK（第9章）用

uv で普段使うのは 2 つだけです。`uv sync` が環境の再現、`uv run <cmd>` がその環境での実行。

## 0.2 【ハンズオン】環境を構築する

### 0.2.1 ツールを導入する

Docker Desktop は公式サイトから入れてください。残りは macOS なら次で揃います。

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

## 次の章

[第1章 Bedrock で Claude を呼び出す](../01-invoke-bedrock/)
