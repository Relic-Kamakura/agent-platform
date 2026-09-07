# 第8章ハンズオンの模範解答。hello-agent/Dockerfile として配置する。
#
# AgentCore Runtime のコンテナ契約: linux/arm64 / 0.0.0.0:8080 / POST /invocations + GET /ping
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1

# 依存だけ先に入れてレイヤを分ける（app.py の変更で再解決させない）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py ./

EXPOSE 8080

# --no-sync: 起動のたびに uv が再ビルドするとコールドスタートが遅くなる
CMD ["uv", "run", "--no-sync", "python", "app.py"]
