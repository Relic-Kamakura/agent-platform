"""ハンズオン 10.3: 外部データを資料として囲む処理。

TODO を実装し、`uv run pytest -q` で判定する。
実装が終わったら TODO の行は消す。完成形は solutions/wrap_result.py。
"""

from __future__ import annotations

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
    # TODO: text に含まれる閉じタグ </search_result> を NEUTRALIZED_TAG へ置換してから囲む。
    #   置換しないと、外部データ側が閉じタグを書くだけで資料の範囲を先に終わらせられる（10.2.3）。
    #   大文字小文字は区別しない。`</SEARCH_RESULT>` も同じ置換の対象にする。
    #   ヒント: re.sub に flags=re.IGNORECASE を渡す。CLOSING_TAG は re.escape でエスケープする。
    body = text
    return f"<search_result>\n{body}\n</search_result>"
