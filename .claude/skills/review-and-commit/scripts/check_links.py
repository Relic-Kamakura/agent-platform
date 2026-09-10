#!/usr/bin/env python3
"""教材内の相対リンクが実在するファイルを指しているかを確かめる。

リポジトリルートで実行する。切れているリンクを `ファイル:行: リンク先` の形で出し、
最後に件数を表示する。0 件でなければ終了コード 1。
"""

from __future__ import annotations

import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
os.chdir(ROOT)

TARGETS = (
    ["README.md", "CLAUDE.md"]
    + glob.glob("*/README.md")
    + glob.glob("*/[0-9]*/README.md")
    + glob.glob("*/[0-9]*/solutions/README.md")
    + glob.glob("docs/*.md")
)

LINK = re.compile(r"\]\(([^)\s#]+)(#[^)]*)?\)")
broken = 0
for path in TARGETS:
    text = open(path, encoding="utf-8").read()
    for match in LINK.finditer(text):
        target = match.group(1)
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
        if not os.path.exists(resolved):
            line = text[: match.start()].count("\n") + 1
            print(f"{path}:{line}: {target}")
            broken += 1

print(f"リンク切れ: {broken} 件")
sys.exit(1 if broken else 0)
