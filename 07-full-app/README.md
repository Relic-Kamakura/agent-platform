# 第7章 完成形を通読する

章であると同時に、動くコードの本体です。ハンズオン課題はありません。代わりに、
第3〜6章の演習とこれ以降の章は、すべてこのディレクトリを改造対象にします。

## 7.1 【ハンズオン】まず動かす

読む前に動かした方が解像度が上がります。

```bash
cd 07-full-app
uv run python -m src.main
```

起動ログの 1 行目に、解決済みモデル ID の一覧が JSON で出ます。
別のターミナルからヘルスチェックを叩きます。

```bash
curl http://127.0.0.1:8080/ping
```

`{"status":"Healthy",...}` が返るはずです。確認したら Ctrl+C で止めてください。

`address already in use` で落ちた場合は、macOS の Docker Desktop が 8080 番を
取っています。ポートを変えて起動し直してください（開発中に踏んだ実話。
troubleshooting.md 参照）。

```bash
SERVER_PORT=8181 uv run python -m src.main
```

## 7.2 1 リクエストの一生

1. `src/main.py` が POST /invocations を受ける。HTTP 契約を知るのはこのファイルだけ
2. Orchestrator (Sonnet) が依頼を調査観点に分解する
3. 観点ごとに investigate ツール = SearchAgent (Haiku) が web_search で調べ、事実と出典を返す
4. Orchestrator が報告に統合する
5. コードが ReviewAgent (Sonnet) を必ず 1 回実行して検証する
6. revise 判定なら修正を 1 回だけ試みて、結果を返す

すべてのエージェントに guards（ツール上限・ターン上限・トークン計測）が付きます。
ガードなしのエージェントはこのリポジトリに存在しません。

## 7.3 ファイルと章の対応

| ファイル | 内容 | 章 |
| --- | --- | --- |
| `src/config.py` | 環境変数を読む唯一の場所。モデル ID 解決 | 1 |
| `src/agents/orchestrator.py` | 分解と統合。Review の決定的実行 | 2, 5 |
| `src/agents/search_agent.py` / `review_agent.py` | 専門エージェント | 5 |
| `src/tools/web_search.py` / `providers/` | ツールの見本と外部 API の作法 | 3 |
| `src/errors.py` | retryable / hint を持つ例外 | 3 |
| `src/guards.py` | 上限ガードとトークン計測 | 4 |
| `src/observability.py` | 構造化ログと request_id | 4 |
| `tests/`（38 件） | LLM を呼ばないテスト | 6 |
| `src/main.py` / `Dockerfile` | エントリポイントとコンテナ | 8 |

## 7.4 普段のコマンド

```bash
uv run pytest
```

```bash
uv run ruff check . && uv run mypy src
```

設定は `cp .env.example .env` して編集します。各値の根拠は `.env.example` の
コメントにあります。`.env` はコミットしないでください。

## 7.5 読み方の提案

`src/main.py`（60 行で骨格が見える）→ `orchestrator.py`（本体）→ `config.py`
（設定の出どころ）の順が最短です。残りは対応する章を進めるときに精読すれば足ります。

## 次の章

[第8章 AgentCore Runtime にデプロイする](../08-agentcore-deploy/)
