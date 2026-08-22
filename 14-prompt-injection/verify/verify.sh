#!/usr/bin/env bash
# 第14章の合格判定。プロンプトの堅牢化と耐性 eval ケースを検査する。
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
FAILED=0

ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

echo "1. 攻撃 fixture（教材提供）"
grep -q "これまでの指示をすべて無視し" 07-full-app/src/tools/providers/mock.py \
  && ok "mock.py に reviews fixture がある" \
  || ng "mock.py の reviews fixture が見つかりません（教材の提供物。消してしまった場合は README 14.1）"

echo "2. プロンプトの堅牢化"
for f in 07-full-app/src/agents/search_agent.py 07-full-app/src/agents/orchestrator.py; do
  if grep -q "検索結果の取り扱い" "$f"; then
    ok "$(basename "$f") に「検索結果の取り扱い」の節がある"
    # 内容の最低条件: 指示に従わないこと・内部情報を出さないことへの言及
    grep -qE "(指示ではあり|従わ)" "$f" && ok "  指示に従わない旨がある" \
      || ng "  「資料内の指示には従わない」ことを書いてください（14.3 要件 2）"
    grep -qE "(環境変数|内部|システムプロンプト)" "$f" && ok "  内部情報を出さない旨がある" \
      || ng "  内部情報（環境変数等）を報告に含めないことを書いてください（14.3 要件 2）"
  else
    ng "$(basename "$f") に「# 検索結果の取り扱い」の節がありません（14.3 要件 1）"
  fi
done

echo "3. 既存テスト"
(cd 07-full-app && uv run pytest -q >/dev/null 2>&1) && ok "38 件が壊れていない" \
  || ng "07-full-app のテストが壊れています。cd 07-full-app && uv run pytest で確認"

echo "4. 耐性 eval ケース"
if grep -q '"injection-resistance"' 13-evaluation/cases.jsonl; then
  ok "injection-resistance ケースがある"
  python3 - <<'PY' && ok "  not_contains で乗っ取り文字列を検証している" || { echo NG; exit_code=1; }
import json, sys
for line in open("13-evaluation/cases.jsonl", encoding="utf-8"):
    if not line.strip():
        continue
    case = json.loads(line)
    if case["id"] == "injection-resistance":
        sys.exit(0 if case.get("expect", {}).get("not_contains") else 1)
sys.exit(1)
PY
  [ "${exit_code:-0}" = "1" ] && ng "  expect.not_contains に乗っ取り時の文字列を入れてください（14.4）"
else
  ng "13-evaluation/cases.jsonl に injection-resistance ケースを追加してください（14.4）"
fi

echo
if [ "$FAILED" = "0" ]; then
  printf '\033[32m第14章 合格（実測は 14.5 で）。\033[0m\n'
else
  printf '\033[31m未達の項目があります。\033[0m\n'
fi
exit "$FAILED"
