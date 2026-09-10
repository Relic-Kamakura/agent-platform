#!/usr/bin/env bash
# 章内完結と禁止表現を機械で拾う。リポジトリルートで実行する。
# 1. 他章への参照（章タイトル行と「次の章」のリンク以外に「第N章」が残っていないか）
# 2. 予告・前提の言い回し
# 3. 記述式の設問
# 4. writing-style / stop-ai-slop-jp が禁じる語と記号
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
FOUND=0

echo "== 1. 他章への参照（タイトルと次の章リンク以外。付録は各章への入口なので対象外）"
for f in */[0-9]*/README.md; do
  case "$f" in */99-appendix/*) continue ;; esac
  hits=$(grep -n -E '第[0-9]+章' "$f" | grep -v -E '^1:# ' | grep -v -E '\]\(\.\./' | grep -v -E '^[0-9]+:## 次の章' | grep -v -E '第[0-9]+章 合格')
  if [ -n "$hits" ]; then echo "--- $f"; echo "$hits"; FOUND=1; fi
done

echo "== 2. 予告・前提の言い回し"
grep -n -E '次の章で|後の章で|後述|で学びます|で扱います|で実装します|で作った|先に終えて|終えていれば' */[0-9]*/README.md && FOUND=1

echo "== 3. 記述式の設問"
grep -n -E '記述・任意|自分の言葉で答え|考えてみてください|説明できますか' */[0-9]*/README.md && FOUND=1

echo "== 4. 禁止表現（全角ダッシュ・空虚な修飾・総括・代弁・口語動詞・界隈語）"
grep -n -E '──|しましょう|強力な|劇的|いちばん|重要なのは|(^|。)まとめると、|重要なポイントは|が分かります|が効きます|を叩く|を回す|走らせる|流す|握りつぶ|静かに壊れ|素の性能|生 HTML|HTTP 契約|コンテナ契約' */[0-9]*/README.md README.md */README.md && FOUND=1

echo "== 5. 文の途中での改行（句点・コロン・記号以外で終わる本文行の直後に本文が続く箇所。参考）"
python3 - <<'PY'
import glob, re
count = 0
for f in sorted(glob.glob('*/[0-9]*/README.md')):
    lines = open(f, encoding='utf-8').read().split('\n')
    incode = False
    for i, l in enumerate(lines[:-1]):
        if l.startswith('```'):
            incode = not incode
            continue
        if incode or not l or l.startswith(('#', '|', '-', '<', '>', ' ', '\t', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
            continue
        nxt = lines[i + 1]
        if nxt and not nxt.startswith(('#', '|', '-', '<', '```', ' ')) and re.search(r'[぀-ヿ一-鿿]$', l):
            count += 1
            if count <= 20:
                print(f"{f}:{i+1}: {l[-20:]!r}")
print(f"文中改行の疑い: {count} 件（読み手の全角空白になる。句点で折り返す）")
PY

if [ "$FOUND" -ne 0 ]; then
  echo; echo "NG: 上の該当箇所を直してください"; exit 1
fi
echo; echo "OK: 他章参照・予告・記述式設問・禁止表現は見つかりませんでした"
