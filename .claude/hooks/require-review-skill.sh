#!/usr/bin/env bash
# PreToolUse フック（Edit / Write / MultiEdit）。
# 教材ファイルを編集する前に review-and-commit スキルの手順に入っているかを確かめる。
# スキルの scripts/start.sh が置くマーカー（12 時間有効）が無ければ編集を止め、理由を返す。
set -uo pipefail

INPUT="$(cat)"
FILE="$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try:
    d=json.load(sys.stdin); ti=d.get("tool_input") or {}
    print(ti.get("file_path") or ti.get("notebook_path") or "")
except Exception:
    print("")')"
[ -n "$FILE" ] || exit 0

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
case "$FILE" in
  "$ROOT"/*) REL="${FILE#"$ROOT"/}" ;;
  /*) exit 0 ;;               # リポジトリ外は対象外
  *) REL="$FILE" ;;
esac

# 対象: 章ディレクトリ、docs、ルートの README / CLAUDE.md、scripts。.claude/ 自身と生成物は対象外
case "$REL" in
  .claude/*|*/.venv/*|*/node_modules/*|*/cdk.out/*|*/__pycache__/*) exit 0 ;;
  1-basic/*|2-advanced/*|3-production/*|docs/*|scripts/*|README.md|CLAUDE.md) ;;
  *) exit 0 ;;
esac

MARKER="$ROOT/.claude/.review-and-commit.active"
if [ -f "$MARKER" ]; then
  now=$(date +%s)
  mtime=$(stat -f %m "$MARKER" 2>/dev/null || stat -c %Y "$MARKER" 2>/dev/null || echo 0)
  if [ $((now - mtime)) -lt $((12 * 3600)) ]; then exit 0; fi
fi

cat >&2 <<EOF
教材ファイル（${REL}）の編集は review-and-commit スキルの手順で行います。
先に Skill ツールで review-and-commit を読み、.claude/skills/review-and-commit/scripts/start.sh を実行してから編集してください。
EOF
exit 2
