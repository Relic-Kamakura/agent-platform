#!/usr/bin/env bash
# 章の合格判定を「素の状態」と「solutions 適用」の両方で実行する。
#   使い方: verify_roundtrip.sh <章ディレクトリ>   例: verify_roundtrip.sh 1-basic/03-tool-design
# 素の状態はリポジトリ内で実行し（案内付きで fail するのが正）、
# solutions 適用は一時ディレクトリへコピーした上で行うので、リポジトリ内の exercises は変わらない。
# 09 / 13 / 16 / 17〜20 のように適用手順が特殊な章は、README の手順に従って手で行う。
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
CH="${1:?章ディレクトリを指定してください（例: 1-basic/03-tool-design）}"
SRC="$ROOT/$CH"
[ -d "$SRC" ] || { echo "見つかりません: $SRC"; exit 1; }

run_verify() {
  local dir="$1"
  if [ -f "$dir/verify/verify.sh" ] && [ ! -d "$dir/verify/__pycache__" ] && ! ls "$dir"/verify/test_*.py >/dev/null 2>&1; then
    (cd "$dir" && ./verify/verify.sh 2>&1 | tail -15)
  else
    (cd "$dir" && uv run pytest -q 2>&1 | tail -8)
  fi
}

echo "===== 素の状態（案内付きで fail するのが正）: $CH"
run_verify "$SRC"

TMP="${TMPDIR:-/tmp}/review-and-commit-roundtrip/$(basename "$CH")"
rm -rf "$TMP" && mkdir -p "$(dirname "$TMP")"
rsync -a --exclude node_modules --exclude .venv --exclude cdk.out --exclude __pycache__ "$SRC/" "$TMP/"
[ -d "$SRC/node_modules" ] && ln -s "$SRC/node_modules" "$TMP/node_modules"
[ -d "$SRC/.venv" ] && ln -s "$SRC/.venv" "$TMP/.venv"

applied=0
if [ -d "$TMP/solutions" ]; then
  for f in "$TMP"/solutions/*; do
    name="$(basename "$f")"
    [ -f "$f" ] || continue
    if [ -f "$TMP/exercises/$name" ]; then cp "$f" "$TMP/exercises/$name"; applied=$((applied+1)); fi
    case "$name" in
      *.ts) mkdir -p "$TMP/lib" && cp "$f" "$TMP/lib/$name" && applied=$((applied+1)) ;;
    esac
  done
fi
echo
echo "===== solutions 適用（$applied ファイルを反映。全パスが正）: $TMP"
if [ "$applied" -eq 0 ]; then
  echo "自動適用できる solutions がありません。README の手順に従って手で適用してください"
  exit 0
fi
run_verify "$TMP"
