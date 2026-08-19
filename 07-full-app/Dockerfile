# AgentCore Runtime 向けコンテナイメージ。
#
# 必ず ARM64 でビルドすること。AgentCore Runtime は linux/arm64 のイメージしか受け付けない。
#   docker buildx build --platform linux/arm64 ...
# --platform を FROM に固定しているのは、x86 のマシンで誤って amd64 イメージを作ると
# デプロイ後の起動時まで気づけないため。
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# 依存だけを先に入れる。src の変更でレイヤキャッシュが壊れないようにするため。
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src

# プロジェクト自体をインストールする（src レイヤの後なので依存は再解決されない）
RUN uv sync --frozen --no-dev

# AgentCore Runtime のコンテナ契約: 0.0.0.0:8080 で /invocations と /ping を提供する
EXPOSE 8080

# --no-sync: これが無いと起動のたびに uv がプロジェクトを再ビルドし、
# AgentCore のコールドスタートがその分だけ遅くなる。
CMD ["uv", "run", "--no-sync", "python", "-m", "src.main"]
