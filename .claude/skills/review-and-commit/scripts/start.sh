#!/usr/bin/env bash
# 教材の編集を許可するマーカーを置く。require-review-skill.sh がこの mtime を見る（12 時間有効）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
MARKER="$ROOT/.claude/.review-and-commit.active"
touch "$MARKER"
echo "review-and-commit の手順で作業を開始しました（$(date '+%Y-%m-%d %H:%M')）。"
echo "次に docs/writing-style.md と .claude/skills/stop-ai-slop-jp/SKILL.md を読んでください。"
