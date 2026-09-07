"""形式の違う入力を parse_verdict_text に渡し、パースが誤判定する様子を見る（編集不要）。"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from review import parse_verdict_text

# どれも書き手（モデル）は approve のつもり。形式が違うだけ
CASES = [
    ("約束どおりの応答      ", "VERDICT: approve\n指摘なし"),
    ("前置きを書いてから判定", "報告を確認しました。結論は以下です。\nVERDICT: approve"),
    ("判定行を言い換えた    ", "判定: approve\n指摘なし"),
    ("判定行を書き忘れた    ", "指摘なし。よくまとまった報告です。"),
]

for label, text in CASES:
    verdict = parse_verdict_text(text)
    first_line = text.splitlines()[0]
    print(f"{label} | 1 行目: {first_line}")
    print(f"{' ' * 22} | パース結果: {verdict.verdict}")
    print()
