# トラブルシューティング

このリポジトリで**実際に遭遇した事象だけ**を記録する。一般的なトラブル集は書かない。
新しい事象に遭遇したら「症状 / 原因 / 対処」の順で追記する。
未遭遇の見出しは空のまま残す。

---

## ローカル実行

### 症状: `pytest` が `MissingDependencyException: botocore[crt]` で失敗する

**原因**
`BedrockModel(...)` はコンストラクタ内で boto3 クライアントを生成するため、
エージェントを組み立てるだけで認証情報の解決が走る。
`aws login` で作られたプロファイル（`login_session`）を解決するには `botocore[crt]` が必要で、
入っていないと例外になる。ネットワークアクセスは発生していない。

**対処**
テストは `07-full-app/tests/conftest.py` でダミーの AWS 認証情報を注入し、環境から独立させている。
アプリを実際に動かす場合は有効な認証情報を用意する。

第1章のように章のスクリプトで実際に Bedrock を呼ぶ場合は、同じ例外が実行時に出る。
その章のディレクトリで `uv add 'botocore[crt]'` を実行して依存に追加する。

### 症状: ローカル起動で `[Errno 48] address already in use`、`curl :8080` が nginx の 404 を返す

**原因**
macOS の Docker Desktop が `127.0.0.1:8080` を LISTEN していることがある。
エージェントは bind に失敗しているが、8080 への curl には Docker 側が応答するため、
一見「起動しているのに 404」に見える。

**対処**
`SERVER_PORT` を変えて起動する（例: `SERVER_PORT=8181 uv run python -m src.main`）。
占有元は `lsof -nP -iTCP:8080 -sTCP:LISTEN` で確認できる。
`SERVER_PORT` はローカル開発専用。コンテナ内は 8080 のままにする。

### 症状: コンテナ外から `/ping` に到達できない

**原因**
`BedrockAgentCoreApp.run()` は `host` を省略すると `127.0.0.1` に bind する。
AgentCore Runtime のコンテナ契約は `0.0.0.0:8080` なので、既定のままでは契約を満たさない。

**対処**
`src/main.py` で `app.run(host=..., port=...)` を明示している（既定 `0.0.0.0:8080`）。
`SERVER_HOST` を変更しないこと。

---

## コンテナビルド

### 症状: コンテナ起動時に "Building agent-platform-agent" が出てコールドスタートが遅い

**原因**
`uv run` は実行のたびにプロジェクトが最新か検証し、必要なら再ビルドする。
イメージに焼いた状態と一致していても検証処理が走る。

**対処**
`Dockerfile` の `CMD` に `--no-sync` を付けている。これでコールドスタートは約 4 秒。

### 症状: `docker buildx build --platform linux/arm64` の警告 `FromPlatformFlagConstDisallowed`

**原因**
`FROM --platform=linux/arm64` のようにプラットフォームを定数で固定すると警告が出る。

**対処**
警告のまま維持している。AgentCore Runtime は arm64 しか受け付けないため、
x86 マシンで誤って amd64 イメージを作らないよう、あえて固定している。

---

## スクリプト

### 症状: `check_env.sh` が arm64 ビルド可能な環境で「linux/arm64 をビルドできません」と誤判定する

**原因**
`docker buildx inspect | grep -q linux/arm64` の形。`grep -q` はマッチした時点でパイプを閉じるため、
上流の `docker buildx inspect` が SIGPIPE で終了する。`set -o pipefail` が有効だと
パイプライン全体が失敗と判定される。マッチしているのに偽陰性になる。

**対処**
先に出力を変数へ取り、`[[ "$VAR" == *"linux/arm64"* ]]` で判定する。
`pipefail` 下では `grep -q` をパイプの終端に置かない。

---

## CDK / インフラ

### 症状: `aws-cdk-lib/aws-bedrockagentcore` の L2 `Runtime` が見つからない

**原因**
aws-cdk-lib 2.264.0 の `aws-bedrockagentcore` が提供するのは L1 (`Cfn*`) のみで、
L2 の `Runtime` / `RuntimeEndpoint` は含まれていない。
（Web 上の解説記事には L2 があるかのような記述があるが、このバージョンには存在しない）

**対処**
`09-infra-as-code/lib/agent-runtime-stack.ts` は `CfnRuntime` を直接使っている。
L2 が入ったバージョンに上げたら移行してよい。確認方法:
`ls node_modules/aws-cdk-lib/aws-bedrockagentcore/lib/`

### 症状: `cdk synth` が `does not match pattern '^[	...ÿ]*$'` の検証警告を出す

**原因**
CloudFormation の `Description` プロパティは ASCII しか受け付けない。日本語を入れると警告になる。

**対処**
CloudFormation に渡す文字列（`description`、`CfnOutput` の説明）は英語にし、
日本語の説明はコードコメントに置く。

---

## デプロイ

### 症状: ECR と Runtime を同時にデプロイすると Runtime の作成が失敗する

**原因**
AgentCore Runtime は作成時点で `containerUri` のイメージが存在している必要がある。
同一デプロイで ECR を新規作成すると、リポジトリが空のまま Runtime 作成に進んでしまう。

**対処**
スタックを分け、`scripts/deploy.sh` が
「ECR デプロイ → イメージ push → Runtime デプロイ」の順序を強制する。
`cdk deploy --all` を直接実行しないこと。

### 症状: ディレクトリ改名後に `uv run` が壊れる

**原因**
`.venv` は生成時の絶対パスを内包している。`mv agent 07-full-app` のように
ディレクトリ名を変えると、venv 内のパスが古いままになり動作しない。

**対処**
改名後に `rm -rf .venv && uv sync` で作り直す。lock ファイルがあるので数秒で同じ環境が再現される。

### 症状: npm install が「No matching version found ... with a date before 2026/8/12」で失敗する

**原因**
この開発機の npm 設定に `before`（日付固定）が入っており、その日付以降に公開された
バージョンを解決できない。`npm view` は最新を表示するため、レジストリ上の存在と
インストール可否が食い違って見える。

**対処**
`npm config get before` で固定日時を確認し、`npm view <pkg> time --json` で
その日付以前の最新バージョンを特定して package.json に固定する。
12-streaming の package.json はこの方針で固定してある。

---

## Bedrock モデル

### 症状: Converse 呼び出しが `ValidationException: The provided model identifier is invalid` で失敗する

**原因**
モデル ID の地理接頭辞が呼び出し元リージョンと合っていない。教材の既定値は
東京前提の `apac.` なので、us-east-1 など他地理のリージョンではそのままだと必ず失敗する。
さらに接頭辞が合っていても、そのモデルの推論プロファイルがリージョンに存在しない
場合は同じ例外になる（今回は us-east-1 に Haiku 4.5 のプロファイルが無かった）。

**対処**
`aws bedrock list-inference-profiles --region <region>` で実在する ID の一覧を確認し、
第1章のスクリプトは環境変数 `MODEL_ID`、本体は `07-full-app/.env` の `MODEL_ID_*` を
一覧にある ID に合わせる。`./scripts/check_env.sh` のセクション 5 がこの確認を自動化している。

---

## 認証 / Cognito

（未遭遇）

---

## フロントエンド / Amplify

（未遭遇）
