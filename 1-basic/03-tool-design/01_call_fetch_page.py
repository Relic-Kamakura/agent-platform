"""fetch_page を自分の手で呼ぶ。成功と失敗の両方を見る（編集不要）。"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from fetch_page import build_fetch_page_tool

tool = build_fetch_page_tool(timeout_seconds=10.0, max_retries=2)
fn = getattr(tool, "__wrapped__", tool)  # @tool のラップを外して元の関数として呼ぶ

print("--- 成功: 実在するページ ---")
print(fn(url="https://example.com", max_chars=200))
print()
print("--- 失敗: 「受け取るもの」に違反する URL ---")
print(fn(url="file:///etc/passwd"))
