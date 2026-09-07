"""ハンズオン 10.3: ミニ RAG。埋め込みの代わりに文字 2-gram の重なりで近さを測る。

TODO を実装し、`uv run 01_search.py` で動かす。
実装が終わったら TODO コメントは消す。完成形は solutions/mini_rag.py。
"""

from __future__ import annotations

DOCUMENTS = [
    "アクメ社は法人向けの経費精算 SaaS を提供している。料金プランは月額の従量課金で、"
    "ユーザー数 50 名までのスタータープランと、SSO と監査ログが付くエンタープライズプランがある。"
    "2025 年にモバイルアプリのレシート OCR 機能を追加した。",
    "ベータ社の主力製品は人事労務の管理ツール。無料トライアルは 30 日間で、"
    "有料化の際は年間契約のみ。カスタマーサポートはメールのみで、導入支援は別料金。"
    "最近は API 連携の拡充を打ち出している。",
    "ガンマ社はチームのタスク管理ツールを開発している。個人利用は無料、"
    "チーム利用は 1 ユーザーあたりの月額課金。強みはガントチャートと外部カレンダー連携で、"
    "大企業よりも中小のソフトウェア開発チームに採用が多い。",
]


def bigrams(text: str) -> set[str]:
    """文字 2-gram の集合を返す。例: "料金プラン" -> {"料金", "金プ", "プラ", "ラン"}"""
    return {text[i : i + 2] for i in range(len(text) - 1)}


def chunk_text(text: str, size: int = 120, overlap: int = 30) -> list[str]:
    """テキストを size 文字のチャンクに分割する。隣り合うチャンクは overlap 文字重ねる。"""
    # TODO(1): 開始位置を size - overlap ずつ進めながら text[start : start + size] を
    #   切り出してリストで返す。先頭チャンクは text[:size]。
    #   末尾のチャンクは size に満たなくてよい。
    ...


def score(query: str, chunk: str) -> float:
    """query と chunk の近さを 0.0〜1.0 で返す。"""
    # TODO(2): クエリ側の 2-gram のうち、チャンクにも現れるものの割合を返す。
    #   query が 1 文字以下で 2-gram が作れないときは 0.0 を返す。
    ...


def retrieve(
    query: str,
    documents: list[str],
    top_k: int = 3,
    size: int = 120,
    overlap: int = 30,
) -> list[tuple[float, str]]:
    """全ドキュメントをチャンクに割り、スコア降順で上位 top_k 件の (スコア, チャンク) を返す。"""
    # TODO(3): 全ドキュメントを chunk_text で分割し、各チャンクに score を付け、
    #   スコア降順に並べて先頭 top_k 件を返す。
    ...
