#!/usr/bin/env python3
"""章 README の分量を測る。

行数と、`N.1 概要` + `N.2 実装のポイント` のコードブロックを除いた日本語文字数を出す。
目安（README 200 行、概要 + ポイント 1,200 字）を超えた章に印を付ける。
16 章のように 2 プロジェクトを持つ章は 240 行まで許容する。
"""

from __future__ import annotations

import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
os.chdir(ROOT)

LINE_LIMIT = 200
LINE_LIMIT_WIDE = {"2-advanced/16-news-kb-mcp/README.md": 240}
CHAR_LIMIT = 1200
JA = re.compile(r"[぀-ヿ一-鿿]")

for path in sorted(glob.glob("*/[0-9]*/README.md")):
    text = open(path, encoding="utf-8").read()
    lines = len(text.splitlines())
    sections = re.split(r"^## ", text, flags=re.M)
    overview = "".join(s for s in sections if re.match(r"\d+\.[12] ", s))
    overview = re.sub(r"```.*?```", "", overview, flags=re.S)
    chars = len(JA.findall(overview))
    limit = LINE_LIMIT_WIDE.get(path, LINE_LIMIT)
    flags = []
    if lines > limit:
        flags.append(f"行数 > {limit}")
    if chars > CHAR_LIMIT:
        flags.append(f"字数 > {CHAR_LIMIT}")
    mark = "  <-- " + " / ".join(flags) if flags else ""
    print(f"{path:45s} {lines:4d} 行  概要+ポイント {chars:5d} 字{mark}")
