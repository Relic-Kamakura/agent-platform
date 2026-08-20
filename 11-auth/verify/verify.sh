#!/usr/bin/env bash
# 第10章の合格判定。synth ベースで AWS 接続は不要。
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT/09-infra-as-code"
FAILED=0

ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

echo "1. AuthStack の存在と型チェック"
if [ ! -f lib/auth-stack.ts ]; then
  ng "lib/auth-stack.ts がありません。README の 10.4.1 に沿って書いてください"
  exit 1
fi
if npx tsc --noEmit >/dev/null 2>&1; then
  ok "tsc --noEmit"
else
  ng "型エラーがあります。npx tsc --noEmit で確認してください"
fi

echo "2. AuthStack の synth"
AUTH="$(CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth AgentPlatformAuthStack 2>/dev/null || true)"
echo "$AUTH" | grep -q "AWS::Cognito::UserPool" && ok "UserPool が定義されている" \
  || ng "AgentPlatformAuthStack に UserPool がありません（bin/app.ts への追加も確認。10.4.2）"
echo "$AUTH" | grep -q "AWS::Cognito::UserPoolClient" && ok "UserPoolClient が定義されている" \
  || ng "App Client がありません（10.4.1 要件 2）"
echo "$AUTH" | grep -q "USER_PASSWORD_AUTH" && ok "USER_PASSWORD_AUTH が有効" \
  || ng "authFlows の userPassword を有効にしてください（10.5 の CLI ログインで使う）"

echo "3. Runtime への配線"
RUNTIME="$(CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth AgentPlatformRuntimeStack 2>/dev/null || true)"
echo "$RUNTIME" | grep -q "CustomJWTAuthorizer" && ok "customJwtAuthorizer が配線されている" \
  || ng "Runtime に JWT authorizer が配線されていません（10.4.2）"
echo "$RUNTIME" | grep -q "well-known/openid-configuration" && ok "DiscoveryUrl が OIDC 形式" \
  || ng "discoveryUrl は /.well-known/openid-configuration まで含めてください（10.2）"

echo
if [ "$FAILED" = "0" ]; then
  printf '\033[32m第10章 合格。\033[0m\n'
else
  printf '\033[31m未達の項目があります。\033[0m\n'
fi
exit "$FAILED"
