# 第7章 完成形を通読する

このディレクトリは章であると同時に、動くコードの本体です。
各章のハンズオンは章内で完結するので、この本体は各章で自作したものの完成形として読み、動かします。
終えると、1 リクエストがどのファイルをどの順に通るか、どのファイルがどの章に対応するかを説明できる状態になります。

依存を先に入れてください。

```bash
cd 07-full-app
uv sync
```

## 7.1 概要

### 7.1.1 3 つのエージェントの役割分担

競合リサーチエージェントです。
調査依頼を受け取り、観点に分解して Web 検索で調べ、報告に統合し、出力を検証するまでを 3 つのエージェントで分担します。
モデルは役割ごとに環境変数で差し替えられ、既定は全役割とも安価な Haiku 4.5 です（docs/versions.md 参照）。
判断が要る Orchestrator と ReviewAgent は、上位モデルに差し替える候補です（第5章）。

この構成には設計判断がひとつあります。
SearchAgent は Orchestrator がツールとして呼びます（agents-as-tools）が、ReviewAgent はモデルの裁量に任せず、`orchestrator.py` のコードで最後に必ず 1 回実行します。
実行するかどうかをモデルの判断に委ねると、検証が省略されることがあるためです。

### 7.1.2 1 リクエストの処理の流れ

```mermaid
graph LR
    CL[クライアント] -->|POST /invocations| M["src/main.py"]
    M --> O["Orchestrator"]
    O -->|investigate ツール| S["SearchAgent"]
    S -->|web_search| P[検索プロバイダ]
    O -.->|コードで必ず 1 回| R["ReviewAgent"]
```

1. `src/main.py` が POST /invocations を受ける。HTTP 契約を知るのはこのファイルだけ
2. Orchestrator が依頼を調査観点に分解する
3. 観点ごとに investigate ツール（実体は SearchAgent）が web_search で調べ、事実と出典を返す
4. Orchestrator が報告に統合する
5. コードが ReviewAgent を必ず 1 回実行して検証する
6. revise 判定なら報告の修正を 1 回だけ試みて、結果を返す

すべてのエージェントに guards（ツール上限とターン上限、トークン計測）が適用されます。

## 7.2 実装のポイント

### 7.2.1 ファイルと章の対応

| ファイル | 内容 | 章 |
| --- | --- | --- |
| `src/config.py` | 環境変数を読む唯一の場所 | 1 |
| `src/agents/orchestrator.py` | 分解と統合、Review の実行 | 2, 5 |
| `src/agents/*_agent.py` | 専門エージェント | 5 |
| `src/tools/` | ツールと外部 API の作法 | 3 |
| `src/errors.py` | retryable を持つ例外 | 3 |
| `src/guards.py` | 上限ガードとトークン計測 | 4 |
| `src/observability.py` | 構造化ログと request_id | 4 |
| `tests/`（38 件） | LLM を呼ばないテスト | 6 |
| `src/main.py` / `Dockerfile` | エントリポイントとコンテナ | 8 |

`src/tools/fetch_page.py` は第3章で自作するものと同じ実装です。
この表はファイルから章を引く向きです。
逆に、開発工程のどこでどの章の話になるかは、[リポジトリ直下の README](../README.md) の工程図を見てください。

### 7.2.2 読む順番

`src/main.py`（80 行で全体の流れが読める）→ `orchestrator.py`（処理の中心）→ `config.py`（設定の出どころ）の順が最短です。
残りは対応する章を進めるときに精読すれば足ります。

### 7.2.3 普段のコマンド

```bash
uv run pytest
```

```bash
uv run ruff check . && uv run mypy src
```

設定は `cp .env.example .env` して編集します。
各値の根拠は `.env.example` のコメントにあります。
`.env` はコミットしないでください。

## 7.3 ハンズオン: 起動して HTTP 契約を確かめる

7.1.2 の入口である `src/main.py` を起動し、コンテナ契約のヘルスチェックが応答することを確認します。

```bash
cd 07-full-app
uv run python -m src.main
```

起動ログの 1 行目に、解決済みモデル ID の一覧が JSON で出ます。
別のターミナルからヘルスチェックを呼びます。

```bash
curl http://127.0.0.1:8080/ping
```

`{"status":"Healthy",...}` が返るはずです。確認したら Ctrl+C で止めてください。

`address already in use` で起動しない場合は、macOS の Docker Desktop が 8080 番を使用しています。
ポートを変えて起動し直してください（[docs/troubleshooting.md](../docs/troubleshooting.md) 参照）。

```bash
SERVER_PORT=8181 uv run python -m src.main
```

## 7.4 まとめ

1 リクエストは main.py → orchestrator.py → search_agent.py → review_agent.py の順に通り、その途中で guards.py が上限を判定し、observability.py がログを出します（7.1.2）。
HTTP 契約は main.py、環境変数は config.py、上限ガードは guards.py と、知る場所を 1 つに絞ってあります。
どのファイルがどの章に対応するかは 7.2.1 の表にあり、章を進めるたびにここへ戻れます。

`uv run pytest` が通ることを確認したら、次は第8章でこの本体をコンテナで動かします。

## 次の章

[第8章 AgentCore Runtime にデプロイする](../08-agentcore-deploy/)
