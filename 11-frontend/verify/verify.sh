#!/usr/bin/env bash
# 第11章の合格判定。AWS 接続は不要（型チェックと実装の構造検査）。
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CHAPTER_DIR"
FAILED=0

ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

echo "1. 依存"
[ -d node_modules ] || { ng "node_modules がありません。npm ci を実行してください"; exit 1; }
ok "npm ci 済み"

echo "2. Route Handler の存在と内容"
ROUTE="app/api/invoke/route.ts"
if [ ! -f "$ROUTE" ]; then
  ng "$ROUTE がありません。README の 11.4 に沿って書いてください"
  exit 1
fi
grep -q "CognitoJwtVerifier" "$ROUTE" && ok "aws-jwt-verify で検証している" \
  || ng "JWT の検証に aws-jwt-verify の CognitoJwtVerifier を使ってください（11.2）"
grep -q "AUTH_BYPASS" "$ROUTE" && ok "AUTH_BYPASS の分岐がある" \
  || ng "開発用の AUTH_BYPASS 分岐を実装してください（11.2）"
grep -q "401" "$ROUTE" && ok "未認証を 401 で返す" \
  || ng "トークン無し・無効時は 401 を返してください"
grep -q "invokeBackend" "$ROUTE" && ok "lib/backend.ts 経由で転送している" \
  || ng "基盤への転送は lib/backend.ts の invokeBackend を使ってください"
grep -qE "upstream.body|\.body," "$ROUTE" && ok "レスポンスをストリームのまま返している" \
  || ng "バックエンドの body を await text() せず、ストリームのまま Response に渡してください（11.3）"

echo "3. 型チェック"
if npx tsc --noEmit >/dev/null 2>&1; then
  ok "tsc --noEmit"
else
  ng "型エラーがあります。npx tsc --noEmit で確認してください"
fi

echo
if [ "$FAILED" = "0" ]; then
  printf '\033[32m第11章 合格。\033[0m\n'
else
  printf '\033[31m未達の項目があります。\033[0m\n'
fi
exit "$FAILED"
