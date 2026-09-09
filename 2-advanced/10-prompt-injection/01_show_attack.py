"""攻撃 fixture を、モデルのコンテキストに入る形のまま表示する（編集不要。オフライン）。"""

import pathlib
import sys

_BASE = pathlib.Path(__file__).parent
sys.path.insert(0, str(_BASE / "exercises"))
sys.path.insert(0, str(_BASE / "fixtures"))

from injected_reviews import as_text
from wrap_result import wrap_as_search_result

print("--- 検索ツールの結果としてモデルのコンテキストに入る文字列 ---")
print(wrap_as_search_result(as_text()))
print()
print("モデルにとって、この中の【指示】と利用者の依頼はどちらも同じテキストです。")
print("区別はプロンプトで教えない限り存在しません。")
