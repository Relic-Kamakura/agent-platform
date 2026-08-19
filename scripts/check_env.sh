#!/usr/bin/env bash
# 前提条件の自動チェック。デプロイで詰まる前に、原因が特定できる形で失敗させる。
#
#   ./scripts/check_env.sh
#
# 何かおかしいときは、まずこれを実行する。
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILED=0

ok()   { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
warn() { printf '  \033[33mWARN\033[0m  %s\n' "$1"; }
ng()   { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }
section() { printf '\n\033[1m%s\033[0m\n' "$1"; }

# --- 1. コマンドの存在 -------------------------------------------------------
section "1. 必要なコマンド"
for cmd in aws docker uv node npm jq; do
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$cmd ($($cmd --version 2>&1 | head -1))"
  else
    ng "$cmd が見つかりません"
  fi
done

# --- 2. ARM64 ビルド環境 -----------------------------------------------------
section "2. コンテナビルド (AgentCore は linux/arm64 のみ受け付ける)"
if docker info >/dev/null 2>&1; then
  ok "Docker デーモンが動作している"
  if docker buildx version >/dev/null 2>&1; then
    ok "docker buildx が利用できる"
    # grep -q はマッチした時点でパイプを閉じるため、上流が SIGPIPE で落ちる。
    # pipefail 有効下ではそれを失敗と見なしてしまうので、先に出力を変数へ取る。
    BUILDX_PLATFORMS="$(docker buildx inspect --bootstrap 2>/dev/null || true)"
    if [[ "$BUILDX_PLATFORMS" == *"linux/arm64"* ]]; then
      ok "linux/arm64 のビルドが可能"
    else
      ng "linux/arm64 をビルドできません。x86 マシンでは QEMU が必要です"
    fi
  else
    ng "docker buildx がありません"
  fi
else
  ng "Docker デーモンに接続できません"
fi

# --- 3. AWS 認証情報 ---------------------------------------------------------
section "3. AWS 認証情報"
IDENTITY="$(aws sts get-caller-identity --output json 2>&1)"
if echo "$IDENTITY" | jq -e '.Account' >/dev/null 2>&1; then
  ACCOUNT="$(echo "$IDENTITY" | jq -r '.Account')"
  ok "認証済み (Account: $ACCOUNT)"
else
  ng "AWS 認証情報が無効です。'aws login' または 'aws sso login' を実行してください"
  echo "        $(echo "$IDENTITY" | head -1)"
fi

# --- 4. リージョン -----------------------------------------------------------
section "4. リージョン"
REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null)}"
if [ -z "$REGION" ]; then
  ng "リージョンが決まりません。AWS_REGION を設定してください"
  REGION="ap-northeast-1"
else
  ok "リージョン: $REGION"
fi
# AgentCore Runtime が使えるリージョンか（2026-08 時点の公式表より）
AGENTCORE_REGIONS="us-east-1 us-east-2 us-west-2 eu-central-1 eu-west-1 eu-west-2 eu-south-1 eu-west-3 eu-south-2 eu-north-1 ap-southeast-5 ap-south-1 ap-southeast-1 ap-southeast-2 ap-southeast-7 ap-northeast-1 ap-northeast-2 ca-central-1 sa-east-1 us-gov-west-1"
if echo "$AGENTCORE_REGIONS" | tr ' ' '\n' | grep -qx "$REGION"; then
  ok "AgentCore Runtime に対応しているリージョン"
else
  warn "$REGION が AgentCore Runtime 対応か未確認です。AWS の Supported AWS Regions を確認してください"
fi

# --- 5. Bedrock モデル ID ----------------------------------------------------
# .env の設定値が実際に呼べる ID かを確認する。
# ここで落としておかないと、原因不明の ValidationException として実行時に現れる。
section "5. Bedrock モデル ID"
ENV_FILE="$REPO_ROOT/07-full-app/.env"
[ -f "$ENV_FILE" ] || ENV_FILE="$REPO_ROOT/07-full-app/.env.example"
get_env() { grep -E "^$1=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2-; }

PREFIX="$(get_env BEDROCK_MODEL_ID_PREFIX)"
if [ -z "$PREFIX" ]; then
  case "$REGION" in
    ap-*) PREFIX="apac" ;;
    us-gov-*) PREFIX="us-gov" ;;
    *) PREFIX="$(echo "$REGION" | cut -d- -f1)" ;;
  esac
fi
ok "推論プロファイル接頭辞: $PREFIX (リージョンから導出)"

PROFILES="$(aws bedrock list-inference-profiles --region "$REGION" --output json 2>/dev/null)"
if echo "$PROFILES" | jq -e '.inferenceProfileSummaries' >/dev/null 2>&1; then
  for role in ORCHESTRATOR SEARCH REVIEW; do
    BASE="$(get_env "MODEL_ID_$role")"
    FULL="$(get_env "MODEL_ID_${role}_FULL")"
    ID="${FULL:-${PREFIX:+$PREFIX.}$BASE}"
    if echo "$PROFILES" | jq -e --arg id "$ID" '.inferenceProfileSummaries[] | select(.inferenceProfileId == $id)' >/dev/null 2>&1; then
      ok "$role: $ID"
    else
      ng "$role: $ID は $REGION の推論プロファイル一覧にありません"
      echo "        利用可能な Claude 系 ID:"
      echo "$PROFILES" | jq -r '.inferenceProfileSummaries[].inferenceProfileId' | grep -i anthropic | sed 's/^/          /' | head -10
    fi
  done
else
  warn "推論プロファイル一覧を取得できませんでした（権限不足か認証切れ）。モデル ID は未検証です"
fi

# --- 6. 結果 -----------------------------------------------------------------
section "結果"
if [ "$FAILED" -eq 0 ]; then
  printf '  \033[32mすべての前提条件を満たしています。\033[0m\n\n'
else
  printf '  \033[31m未達の項目があります。上の NG を解消してください。\033[0m\n\n'
fi
exit "$FAILED"
