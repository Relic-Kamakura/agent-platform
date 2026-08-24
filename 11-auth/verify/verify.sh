#!/usr/bin/env bash
# 第11章の合格判定。型チェックと synth の結果を検査する。
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CHAPTER_DIR"
FAILED=0

ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

echo "1. 前提"
if [ ! -d node_modules ]; then
  ng "依存が入っていません。11-auth で npm ci を実行してください"
  exit 1
fi
if [ ! -f lib/auth-stack.ts ]; then
  ng "lib/auth-stack.ts がありません。exercises/auth-stack.ts をコピーして TODO を埋めてください（11.3.1）"
  exit 1
fi
if grep -q "TODO" lib/auth-stack.ts; then
  ng "lib/auth-stack.ts に TODO が残っています。README 11.3 に沿って実装し、終わったら TODO コメントを消してください"
  exit 1
fi
ok "lib/auth-stack.ts がある"

echo "2. 型チェック"
if npx tsc --noEmit >/dev/null 2>&1; then
  ok "tsc --noEmit"
else
  ng "型エラーがあります。npx tsc --noEmit で確認してください"
fi

echo "3. synth"
SYNTH="$(npx cdk synth AgentPlatformAuthStack 2>/dev/null || true)"
echo "$SYNTH" | grep -q "AWS::Cognito::UserPool" && ok "UserPool が定義されている" \
  || ng "UserPool がありません（11.3.1 TODO(1)）"
echo "$SYNTH" | grep -q "AWS::Cognito::UserPoolClient" && ok "UserPoolClient が定義されている" \
  || ng "App Client がありません（11.3.1 TODO(2)）"
echo "$SYNTH" | grep -q "USER_PASSWORD_AUTH" && ok "USER_PASSWORD_AUTH が有効" \
  || ng "authFlows の userPassword を有効にしてください（11.4 の CLI ログインで使う）"
echo "$SYNTH" | grep -q "well-known/openid-configuration" && ok "DiscoveryUrl が OIDC 形式" \
  || ng "discoveryUrl は /.well-known/openid-configuration まで含めてください（11.1.3）"
echo "$SYNTH" | grep -q "UserPoolId" && ok "CfnOutput がある" \
  || ng "UserPoolId などの CfnOutput を出してください（11.3.1 TODO(4)）"

echo
if [ "$FAILED" = "0" ]; then
  printf '\033[32m第11章 合格。\033[0m\n'
else
  printf '\033[31m未達の項目があります。\033[0m\n'
fi
exit "$FAILED"
