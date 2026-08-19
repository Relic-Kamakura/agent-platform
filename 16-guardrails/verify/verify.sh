#!/usr/bin/env bash
# 第16章の合格判定。synth と配線の検査（AWS 不要）。
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAILED=0
ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

echo "1. GuardrailStack"
cd "$REPO_ROOT/09-infra-as-code"
if [ ! -f lib/guardrail-stack.ts ]; then
  ng "lib/guardrail-stack.ts がありません（README 16.3）"
else
  npx tsc --noEmit >/dev/null 2>&1 && ok "tsc --noEmit" || ng "型エラーがあります"
  SYNTH="$(CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth AgentPlatformGuardrailStack 2>/dev/null || true)"
  echo "$SYNTH" | grep -q "AWS::Bedrock::Guardrail" && ok "CfnGuardrail が定義されている" \
    || ng "AgentPlatformGuardrailStack に Guardrail がありません（bin/app.ts への追加も確認）"
  echo "$SYNTH" | grep -q "PROMPT_ATTACK" && ok "PROMPT_ATTACK フィルタがある" \
    || ng "contentPolicyConfig に PROMPT_ATTACK フィルタを入れてください（16.3 要件 1）"
  echo "$SYNTH" | grep -q "AWS::Bedrock::GuardrailVersion" && ok "版を発行している" \
    || ng "CfnGuardrailVersion で版を発行してください（16.3 要件 2）"
fi

echo "2. アプリ側の配線"
cd "$REPO_ROOT"
uv run --project 07-full-app python - <<'PY' && ok "guardrail 設定がモデルに渡る" || ng "config/models の配線が未完です（16.3 要件 5-6）"
import os, sys
os.environ.update(AWS_ACCESS_KEY_ID="t", AWS_SECRET_ACCESS_KEY="t")
sys.path.insert(0, "07-full-app")
from src.config import Settings
from src.agents.models import build_model

s = Settings(guardrail_id="gid", guardrail_version="1")
c = build_model(s, "search").get_config()
assert c.get("guardrail_id") == "gid" and c.get("guardrail_version") == "1"
# 未設定なら渡さない
c2 = build_model(Settings(), "search").get_config()
assert c2.get("guardrail_id") is None
PY

echo
[ "$FAILED" = "0" ] && printf '\033[32m第16章 合格。\033[0m\n' || printf '\033[31m未達の項目があります。\033[0m\n'
exit "$FAILED"
