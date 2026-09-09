"""ハンズオン 10.3 の完成形: 外部データを資料として囲む処理。"""

from __future__ import annotations

import re

CLOSING_TAG = "</search_result>"
# 閉じタグの置き換え先。全角の括弧なのでタグの終わりとしては読めない形になり、
# 何が書かれていたかは報告に残る
NEUTRALIZED_TAG = "〈/search_result〉"


def wrap_as_search_result(text: str) -> str:
    """外部データを <search_result> タグで囲み、資料の範囲を示す。

    受け取るもの: text。検索ツールが取得した第三者のテキスト。
    返すもの: <search_result> タグで囲んだ文字列。
    含まないもの: 内容の真偽の判定。
    """
    # 外部データ側も閉じタグを書けるので、囲む前に無害な文字へ置換して資料の範囲を保つ。
    # 大文字で書かれた `</SEARCH_RESULT>` も同じ対象にするため IGNORECASE を付ける
    body = re.sub(re.escape(CLOSING_TAG), NEUTRALIZED_TAG, text, flags=re.IGNORECASE)
    return f"<search_result>\n{body}\n</search_result>"
