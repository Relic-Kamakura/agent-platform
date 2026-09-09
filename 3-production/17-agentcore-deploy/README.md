# 第17章 AgentCore Runtime にデプロイする

この章を終えると、AgentCore Runtime が受け付けるコンテナの条件を説明でき、それを満たす Dockerfile を自分で書いて、デプロイ前にローカルで検証できるようになります。

章のディレクトリへ移動します。追加で入れる依存はありません。

```bash
cd 3-production/17-agentcore-deploy
```

Docker Desktop を起動し、ビルダーが ARM64 に対応しているかを確認します。

```bash
docker buildx inspect --bootstrap
```

`Platforms:` の行に `linux/arm64` が含まれているはずです。含まれていなければ、x86 マシンでは QEMU の設定が要ります。

## 17.1 概要

### 17.1.1 AgentCore Runtime

エージェントのコードをコンテナとしてホストするサーバレス実行基盤です。
セッションごとに専用の microVM が起動し、CPU とメモリとファイルシステムがセッション間で分離され、セッション終了時に microVM ごと破棄されます。
課金は消費した CPU とメモリに基づき、事前のキャパシティ確保は要りません。

VPC を用意しなくても外部へ出られるため、このリポジトリはネットワークをマネージドに任せています。実行時間、ペイロード、イメージサイズの上限は versions.md にまとめてあります。

AgentCore CLI（`agentcore create` から `agentcore deploy`）でも、コンテナに要求される条件は同じです。
この章は自分で ARM64 イメージを作って ECR に push し、実行ロールとデプロイ順序を CDK で書く方法を採ります。

### 17.1.2 Runtime がコンテナに要求する条件

Runtime がコンテナに要求するのは 3 点です。

- アーキテクチャ: linux/arm64 のみ
- エンドポイント: `POST /invocations`（本体）と `GET /ping`（ヘルスチェック）
- バインド: `0.0.0.0:8080`

このポートとパスは、Runtime の `protocolConfiguration` が既定の HTTP のときの値です。
MCP を選ぶと 8000 番の `/mcp`、A2A を選ぶと 9000 番の `/` に変わります。
`0.0.0.0` に bind することと ARM64 であることは、どのプロトコルでも共通です。

要求はこの 3 点だけで、フレームワークは指定されていません。中身は Strands でも LangGraph でも自作でもよく、乗り換えるときに書き換えるのはエントリポイントの 1 ファイルだけです。

`bedrock_agentcore.runtime.BedrockAgentCoreApp` がこの 3 点を実装しており、`@app.entrypoint` を付けた関数を書くだけで 2 つのエンドポイントが用意されます。

`app.run()` は host を省略すると、`/.dockerenv` の有無と環境変数 `DOCKER_CONTAINER` を見て bind 先を決め、どちらも見つからなければ 127.0.0.1 に bind します（bedrock-agentcore のソースで確認。バージョンは versions.md）。
Runtime の microVM に `/.dockerenv` があるかは公開されていないので、自動判定には任せず `host="0.0.0.0"` を明示します。

## 17.2 実装のポイント

この 3 点をイメージの側で満たすのが Dockerfile です。30 行ほどですが、各行に理由があります。

`FROM --platform=linux/arm64` でプラットフォームを固定します。x86 マシンで誤って amd64 のイメージを作ると、デプロイして起動するまで気づけません。

依存レイヤと src レイヤは分けます。pyproject.toml と uv.lock だけを先に COPY して `uv sync --frozen --no-dev` を実行し、ソースは後から別のレイヤで COPY します。コード 1 行の修正で依存の再解決が走らないようにするためです。

`CMD` の `uv run` に `--no-sync` を付けないと、uv が起動のたびにプロジェクトを検証して再ビルドします。
付けた場合と付けない場合のコールドスタートの実測値は versions.md にあります。
コールドスタートは新しいセッションの初回応答にそのまま乗るので、この差は利用者の待ち時間の差です。

## 17.3 ハンズオン: 本体イメージをビルドして要求条件を検証する

完成形のエージェント（`1-basic/07-full-app`）をイメージにして、17.1.2 の 3 点をローカルで検査します。この本体は Strands のエージェントを `BedrockAgentCoreApp` で包んだもので、Dockerfile も同梱されています。

### 17.3.1 ARM64 イメージをビルドする

```bash
docker buildx build --platform linux/arm64 -t agent-platform/agent:local --load ../../1-basic/07-full-app
```

```bash
docker image inspect agent-platform/agent:local --format '{{.Os}}/{{.Architecture}}'
```

`linux/arm64` と出るはずです。

### 17.3.2 /ping と /invocations が応答することを確かめる

```bash
docker run -d --name agent-local -p 8181:8080 \
  -e AWS_ACCESS_KEY_ID=dummy -e AWS_SECRET_ACCESS_KEY=dummy \
  -e AWS_DEFAULT_REGION=ap-northeast-1 \
  agent-platform/agent:local
```

```bash
curl http://127.0.0.1:8181/ping
```

`{"status":"Healthy",...}` が返るはずです。

```bash
curl -XPOST http://127.0.0.1:8181/invocations \
  -H 'Content-Type: application/json' -d '{"prompt":""}'
```

`{"error": "payload に 'prompt' が必要です。", ...}` が返るはずです。空プロンプトはモデルを呼ばずにエラー応答を返す設計なので、ローカルのコンテナだけで 2 つのエンドポイントを検証できます。終わったら片付けます。

```bash
docker rm -f agent-local
```

## 17.4 ハンズオン: Dockerfile を自分で書く

今度は 17.1.2 の 3 点を自分の手で満たします。`hello-agent/` に LLM を呼ばないミニエージェント（app.py と pyproject.toml）を用意してあり、無いのは Dockerfile だけです。

### 17.4.1 TODO を 4 個埋める

```bash
cp exercises/Dockerfile hello-agent/Dockerfile
```

`hello-agent/Dockerfile` を開いてください。
WORKDIR と ENV は書いてあり、TODO が 4 つ残っています。

1. FROM で uv の Python ベースイメージ（バージョンは versions.md）を linux/arm64 に固定する
2. 依存レイヤを分離する。pyproject.toml と uv.lock を先に入れ、app.py は後から別レイヤで COPY する
3. EXPOSE で Runtime が接続するポート 8080 を宣言する
4. CMD で uv run から app.py を起動する。コールドスタート対策も入れる

埋める材料はすべて 17.2 にあります。埋めたら TODO コメントは消してください。

### 17.4.2 実行する

```bash
docker buildx build --platform linux/arm64 -t hello-agent:local --load hello-agent
```

```bash
docker run -d --name hello-local -p 18081:8080 hello-agent:local
```

```bash
curl http://127.0.0.1:18081/ping
```

`{"status":"Healthy",...}` が返るはずです。

```bash
curl -XPOST http://127.0.0.1:18081/invocations -H 'Content-Type: application/json' -d '{"prompt":"test"}'
```

`{"echo": "test", "chapter": 17}` が返るはずです。片付けます。

```bash
docker rm -f hello-local
```

<details>
<summary>解答例</summary>

```dockerfile
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py ./

EXPOSE 8080

CMD ["uv", "run", "--no-sync", "python", "app.py"]
```

コメント付きの全文は `solutions/hello-agent.Dockerfile` にあります。

</details>

### 17.4.3 合格判定

verify.sh が本体（17.3）と自作 Dockerfile（17.4）の両方を判定します。

```bash
./verify/verify.sh
```

## 17.5 ハンズオン: デプロイして 1 回呼び出す

```bash
../../scripts/deploy.sh
```

ECR 作成、ARM64 イメージの push、Runtime 作成の順で進みます。
Runtime は作成時点で ECR にイメージがあることを要求するので、この順序をスクリプトが強制しています。
完了メッセージに出力される `InvokeAgentRuntime` の呼び出し例を実行し、CloudWatch Logs で `token_usage` のログを確認してください。
セッション ID には最小長の制約があり（versions.md）、例はそれを満たす形になっています。

## 17.6 まとめ

AgentCore Runtime が決めているのは arm64、2 エンドポイント、`0.0.0.0:8080` の 3 点だけで、コンテナの中身には関与しません。
要求が 3 点だけなのでデプロイ前にローカルで検証を済ませられ、条件を満たさないイメージを push してから気づく事態を避けられます。
`verify/verify.sh` を通してから次へ進んでください。

## 次の章

[第18章 基盤をコードで定義する](../18-infra-as-code/)
