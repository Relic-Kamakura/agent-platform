"""exercises の retrieve を自分の手で呼び、上位 3 件のスコアとチャンクを見る（編集不要）。"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from mini_rag import DOCUMENTS, retrieve

for s, c in retrieve("無料トライアルの期間は？", DOCUMENTS, top_k=3):
    print(f"{s:.2f} | {c[:40]}")
