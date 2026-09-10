#!/usr/bin/env bash
# 全 README の ```mermaid ブロックを mermaid（npm）で解析し、描けないものを報告する。
# 初回は ${TMPDIR:-/tmp}/review-and-commit-mermaid に mermaid と jsdom を入れる（AWS は使わない）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE="${TMPDIR:-/tmp}/review-and-commit-mermaid"

mkdir -p "$CACHE"
if [ ! -d "$CACHE/node_modules/mermaid" ] || [ ! -d "$CACHE/node_modules/jsdom" ]; then
  echo "mermaid と jsdom を $CACHE に入れます（初回のみ）"
  (cd "$CACHE" && npm install --silent --no-audit --no-fund mermaid jsdom)
fi

cd "$ROOT"
python3 - > "$CACHE/blocks.json" <<'PY'
import glob, json
out = []
files = ['README.md'] + sorted(glob.glob('*/README.md')) + sorted(glob.glob('*/[0-9]*/README.md')) + sorted(glob.glob('docs/*.md'))
for f in files:
    lines = open(f, encoding='utf-8').read().split('\n')
    i = 0
    while i < len(lines):
        if lines[i].startswith('```mermaid'):
            j = i + 1
            while j < len(lines) and not lines[j].startswith('```'):
                j += 1
            out.append({"file": f, "line": i + 1, "text": '\n'.join(lines[i + 1:j])})
            i = j
        i += 1
print(json.dumps(out, ensure_ascii=False))
PY

cp "$SCRIPT_DIR/check_mermaid.mjs" "$CACHE/check_mermaid.mjs"
(cd "$CACHE" && node check_mermaid.mjs)
