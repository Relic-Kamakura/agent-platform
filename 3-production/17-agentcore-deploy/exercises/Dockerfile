# ハンズオン 8.4: AgentCore のコンテナ契約を満たす Dockerfile の骨組み。
# hello-agent/Dockerfile にコピーして TODO を埋め、埋めたら TODO コメントは消す。
# 完成形は solutions/hello-agent.Dockerfile。

# TODO(1): ベースイメージを書く。
#   - uv の Python 3.12 イメージ ghcr.io/astral-sh/uv:python3.12-bookworm-slim を使う
#   - FROM --platform=linux/arm64 で固定する（固定する理由は 8.2）

WORKDIR /app

ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1

# TODO(2): 依存レイヤを分ける。
#   - pyproject.toml と uv.lock だけを先に COPY し、RUN uv sync --frozen --no-dev で依存を入れる
#   - app.py の COPY はその後に別の行で書く（分ける理由は 8.2）

# TODO(3): 契約のポート 8080 を EXPOSE する

# TODO(4): CMD を exec 形式（JSON 配列）で書き、uv run で app.py を起動する。
#   - uv run には --no-sync を付ける（付けない場合に起きることは 8.2）
