"""攻撃 fixture を、モデルのコンテキストに入る形のまま表示する（編集不要。オフライン）。"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "fixtures"))

from injected_reviews import as_tool_result

print("--- 検索ツールの結果としてモデルのコンテキストに入る文字列 ---")
print(as_tool_result())
print()
print("モデルにとって、この中の【指示】と利用者の依頼はどちらも同じテキストです。")
print("区別はプロンプトで教えない限り存在しません。")
