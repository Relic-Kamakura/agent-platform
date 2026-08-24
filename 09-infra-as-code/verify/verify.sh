#!/usr/bin/env bash
# 演習 09 の合格判定: context -> Runtime 環境変数の注入。AWS 接続は不要。
set -uo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$INFRA_DIR"
FAILED=0

ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

echo "1. 型チェック"
if npx tsc --noEmit >/dev/null 2>&1; then
  ok "tsc --noEmit"
else
  ng "型エラーがあります。npx tsc --noEmit で確認してください"
fi

echo "2. cdk.json の既定値"
if jq -e '.context.logLevel' cdk.json >/dev/null 2>&1; then
  ok 'context に logLevel の既定値がある'
else
  ng 'cdk.json の context に "logLevel" を追加してください（README 9.3.2）'
fi

echo "3. synth への反映 (-c logLevel=DEBUG)"
SYNTH="$(CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth AgentPlatformRuntimeStack -c logLevel=DEBUG 2>/dev/null || true)"
if echo "$SYNTH" | grep -q "LOG_LEVEL: DEBUG"; then
  ok "Runtime の EnvironmentVariables に LOG_LEVEL: DEBUG が入っている"
else
  ng "synth 結果に LOG_LEVEL: DEBUG がありません。lib/config.ts の agentEnvironment を確認してください（README 9.3.1）"
fi

echo "4. 未指定なら注入しない"
SYNTH_DEFAULT="$(CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth AgentPlatformRuntimeStack 2>/dev/null || true)"
if echo "$SYNTH_DEFAULT" | grep -q "LOG_LEVEL: INFO"; then
  ok "既定値 INFO が cdk.json から入っている"
else
  ng "既定（cdk.json の logLevel=INFO）が synth に反映されていません（README 9.3.2）"
fi

echo
if [ "$FAILED" = "0" ]; then
  printf '\033[32m演習 09 合格。\033[0m\n'
else
  printf '\033[31m未達の項目があります。\033[0m\n'
fi
exit "$FAILED"
