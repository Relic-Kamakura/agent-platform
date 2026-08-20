"""ミニ RAG。埋め込みの代わりに文字 2-gram の重なりで近さを測る。"""

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
    step = size - overlap
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        if start + size >= len(text):
            break
        start += step
    return chunks


def score(query: str, chunk: str) -> float:
    """query と chunk の近さを 0.0〜1.0 で返す。

    クエリ側の 2-gram のうち、チャンクにも現れるものの割合。
    query が 1 文字以下で 2-gram が作れないときは 0.0。
    """
    q = bigrams(query)
    if not q:
        return 0.0
    return len(q & bigrams(chunk)) / len(q)


def retrieve(
    query: str,
    documents: list[str],
    top_k: int = 3,
    size: int = 120,
    overlap: int = 30,
) -> list[tuple[float, str]]:
    """全ドキュメントをチャンクに割り、スコア降順で上位 top_k 件の (スコア, チャンク) を返す。"""
    chunks = [c for doc in documents for c in chunk_text(doc, size, overlap)]
    ranked = sorted(((score(query, c), c) for c in chunks), key=lambda t: t[0], reverse=True)
    return ranked[:top_k]


if __name__ == "__main__":
    for s, c in retrieve("無料トライアルの期間は？", DOCUMENTS, top_k=3):
        print(f"{s:.2f} | {c[:40]}")
