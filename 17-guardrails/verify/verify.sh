#!/usr/bin/env bash
# 第17章（CDK 側）の合格判定。型チェックと synth の結果を検査する。
# アプリ側は `uv run pytest -q` で判定する。
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CHAPTER_DIR"
FAILED=0

ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

echo "1. 前提"
if [ ! -d node_modules ]; then
  ng "依存が入っていません。17-guardrails で npm ci を実行してください"
  exit 1
fi
if [ ! -f lib/guardrail-stack.ts ]; then
  ng "lib/guardrail-stack.ts がありません。exercises/guardrail-stack.ts をコピーして TODO を埋めてください（17.3.1）"
  exit 1
fi
if grep -q "TODO" lib/guardrail-stack.ts; then
  ng "lib/guardrail-stack.ts に TODO が残っています。README 17.3 に沿って実装し、終わったら TODO コメントを消してください"
  exit 1
fi
ok "lib/guardrail-stack.ts がある"

echo "2. 型チェック"
if npx tsc --noEmit >/dev/null 2>&1; then
  ok "tsc --noEmit"
else
  ng "型エラーがあります。npx tsc --noEmit で確認してください"
fi

echo "3. synth"
SYNTH="$(npx cdk synth AgentPlatformGuardrailStack 2>/dev/null || true)"
echo "$SYNTH" | grep -q "AWS::Bedrock::Guardrail" && ok "CfnGuardrail が定義されている" \
  || ng "Guardrail がありません（17.3.1）"
echo "$SYNTH" | grep -q "PROMPT_ATTACK" && ok "PROMPT_ATTACK フィルタがある" \
  || ng "contentPolicyConfig に PROMPT_ATTACK フィルタを入れてください（17.3.1 TODO(1)）"
echo "$SYNTH" | grep -q "AWS::Bedrock::GuardrailVersion" && ok "版を発行している" \
  || ng "CfnGuardrailVersion で版を発行してください（17.3.1 TODO(2)）"
echo "$SYNTH" | grep -q "GuardrailId" && ok "CfnOutput がある" \
  || ng "GuardrailId などの CfnOutput を出してください（17.3.1 TODO(3)）"

echo
if [ "$FAILED" = "0" ]; then
  printf '\033[32m第17章（CDK 側）合格。アプリ側は uv run pytest -q で判定してください。\033[0m\n'
else
  printf '\033[31m未達の項目があります。\033[0m\n'
fi
exit "$FAILED"
