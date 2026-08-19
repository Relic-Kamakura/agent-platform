#!/usr/bin/env bash
# 演習 08 の合格判定: ARM64 ビルドと AgentCore コンテナ契約の検証。
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

IMAGE="agent-platform/agent:verify08"
CONTAINER="agent-verify08"
PORT=18080
FAILED=0

ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

cleanup() { docker rm -f "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "1. ARM64 イメージのビルド"
if docker buildx build --platform linux/arm64 -t "$IMAGE" --load 07-full-app >/dev/null 2>&1; then
  ok "ビルド成功"
else
  ng "ビルド失敗。docker buildx build --platform linux/arm64 07-full-app を手で実行して原因を見る"
  exit 1
fi

echo "2. アーキテクチャ"
ARCH="$(docker image inspect "$IMAGE" --format '{{.Os}}/{{.Architecture}}')"
if [ "$ARCH" = "linux/arm64" ]; then
  ok "linux/arm64"
else
  ng "アーキテクチャが $ARCH です。AgentCore Runtime は linux/arm64 のみ受け付けます"
fi

echo "3. コンテナ契約 (/ping と /invocations)"
cleanup
docker run -d --name "$CONTAINER" -p "$PORT:8080" \
  -e AWS_ACCESS_KEY_ID=dummy -e AWS_SECRET_ACCESS_KEY=dummy \
  -e AWS_DEFAULT_REGION=ap-northeast-1 \
  "$IMAGE" >/dev/null

PING_OK=0
for _ in $(seq 1 30); do
  sleep 1
  CODE="$(curl -s -m 3 -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/ping" 2>/dev/null || true)"
  if [ "$CODE" = "200" ]; then PING_OK=1; break; fi
done
if [ "$PING_OK" = "1" ]; then
  ok "GET /ping -> 200"
else
  ng "GET /ping が 200 になりません。docker logs $CONTAINER を確認（127.0.0.1 bind の罠は troubleshooting.md）"
fi

INVOKE_CODE="$(curl -s -m 10 -o /tmp/verify08_invoke.json -w '%{http_code}' \
  -XPOST "http://127.0.0.1:$PORT/invocations" \
  -H 'Content-Type: application/json' -d '{"prompt":""}' 2>/dev/null || true)"
if [ "$INVOKE_CODE" = "200" ] && grep -q "prompt" /tmp/verify08_invoke.json; then
  ok "POST /invocations -> 200 (空プロンプトのエラー応答)"
else
  ng "POST /invocations が期待どおり応答しません (HTTP $INVOKE_CODE)"
fi

echo "4. 自作 Dockerfile (hello-agent)"
HELLO_DIR="$REPO_ROOT/08-agentcore-deploy/hello-agent"
if [ ! -f "$HELLO_DIR/Dockerfile" ]; then
  ng "hello-agent/Dockerfile がありません。README の 8.5 に沿って自分で書いてください"
else
  if docker buildx build --platform linux/arm64 -t hello-agent:verify08 --load "$HELLO_DIR" >/dev/null 2>&1; then
    ok "自作 Dockerfile でビルド成功"
    HARCH="$(docker image inspect hello-agent:verify08 --format '{{.Os}}/{{.Architecture}}')"
    [ "$HARCH" = "linux/arm64" ] && ok "linux/arm64" || ng "アーキテクチャが $HARCH です"
    docker rm -f hello-verify08 >/dev/null 2>&1 || true
    docker run -d --name hello-verify08 -p 18082:8080 hello-agent:verify08 >/dev/null
    HOK=0
    for _ in $(seq 1 20); do
      sleep 1
      CODE="$(curl -s -m 3 -o /dev/null -w '%{http_code}' "http://127.0.0.1:18082/ping" 2>/dev/null || true)"
      [ "$CODE" = "200" ] && HOK=1 && break
    done
    if [ "$HOK" = "1" ]; then
      BODY="$(curl -s -m 5 -XPOST http://127.0.0.1:18082/invocations -H 'Content-Type: application/json' -d '{"prompt":"test"}')"
      echo "$BODY" | grep -q '"echo": *"test"' && ok "POST /invocations -> echo 応答" \
        || ng "/invocations の応答が想定と違います: $BODY"
    else
      ng "自作コンテナの /ping が 200 になりません（0.0.0.0 bind か CMD を確認。8.2 の罠参照）"
    fi
    docker rm -f hello-verify08 >/dev/null 2>&1 || true
  else
    ng "自作 Dockerfile のビルドが失敗しました。手でビルドしてエラーを確認してください"
  fi
fi

echo
if [ "$FAILED" = "0" ]; then
  printf '\033[32m第8章 合格。\033[0m\n'
else
  printf '\033[31m未達の項目があります。\033[0m\n'
fi
exit "$FAILED"
