#!/usr/bin/env bash
# CDK デプロイのラッパー。
#
#   ./scripts/deploy.sh
#
# 順序を強制するためのスクリプト。
# AgentCore Runtime は作成時点で ECR にイメージが存在している必要があるため、
# ECR と Runtime を同一デプロイで作ると Runtime 作成が失敗する。
#   1. ECR スタックをデプロイ
#   2. ARM64 イメージをビルドして push
#   3. Runtime スタックをデプロイ
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

REGION="${AWS_REGION:-$(cd 09-infra-as-code && npx --no-install cdk context --json 2>/dev/null | jq -r '.region // empty' 2>/dev/null || true)}"
REGION="${REGION:-$(aws configure get region)}"
[ -n "$REGION" ] || { echo "リージョンが決まりません。AWS_REGION を設定してください。" >&2; exit 1; }

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
REPO_NAME="$(jq -r '.context.ecrRepositoryName' 09-infra-as-code/cdk.json)"
IMAGE_TAG="$(jq -r '.context.imageTag' 09-infra-as-code/cdk.json)"
REGISTRY="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_URI="${REGISTRY}/${REPO_NAME}:${IMAGE_TAG}"

echo "Account : $ACCOUNT"
echo "Region  : $REGION"
echo "Image   : $IMAGE_URI"

step "0/3 前提条件チェック"
./scripts/check_env.sh

step "1/3 ECR スタックをデプロイ"
(cd 09-infra-as-code && npx cdk deploy AgentPlatformEcrStack -c region="$REGION" --require-approval never)

step "2/3 ARM64 イメージをビルドして push"
# --platform linux/arm64 は必須。AgentCore Runtime は arm64 のイメージしか起動できない。
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"
docker buildx build \
  --platform linux/arm64 \
  --provenance=false \
  -t "$IMAGE_URI" \
  --push \
  07-full-app

step "3/3 Runtime スタックをデプロイ"
(cd 09-infra-as-code && npx cdk deploy AgentPlatformRuntimeStack -c region="$REGION" --require-approval never)

step "完了"
RUNTIME_ARN="$(aws cloudformation describe-stacks \
  --stack-name AgentPlatformRuntimeStack --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" --output text)"
echo "Runtime ARN: $RUNTIME_ARN"
echo
echo "呼び出し例 (session-id は 33 文字以上が必要):"
echo "  aws bedrock-agentcore invoke-agent-runtime \\"
echo "    --agent-runtime-arn '$RUNTIME_ARN' \\"
echo "    --runtime-session-id \"\$(uuidgen | tr -d - )\$(date +%s)\" \\"
echo "    --payload '{\"prompt\":\"Acme と Globex の pricing と feature を比較して\"}' \\"
echo "    --region $REGION /dev/stdout"
