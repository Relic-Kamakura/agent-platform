"""第10章の合格判定。要求仕様のテスト表現でもある。"""

from __future__ import annotations

import pathlib

import mini_rag as impl  # conftest が exercises/ を import パスに足している


def test_no_todo_left() -> None:
    source = pathlib.Path(impl.__file__).read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/mini_rag.py に TODO が残っています。README 10.3 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


def test_chunk_shape() -> None:
    chunks = impl.chunk_text("abcdefghij", size=4, overlap=2)
    assert chunks is not None, "chunk_text が未実装です。README 10.3 の TODO(1) を実装してください。"
    assert all(len(c) <= 4 for c in chunks), (
        "size を超えるチャンクがあります。text[start : start + size] で切り出してください。"
    )
    assert chunks[0] == "abcd", "先頭チャンクは text[:size] になるはずです。"
    for left, right in zip(chunks, chunks[1:]):
        assert left[-2:] == right[:2], (
            "隣り合うチャンクが overlap 文字重なっていません。開始位置は size - overlap ずつ進めます。"
        )


def test_chunk_covers_whole_text() -> None:
    text = "0123456789" * 30
    chunks = impl.chunk_text(text, size=120, overlap=30)
    assert chunks, "chunk_text が未実装です。README 10.3 の TODO(1) を実装してください。"
    rebuilt = chunks[0] + "".join(c[30:] for c in chunks[1:])
    assert rebuilt == text, (
        "チャンクを繋ぎ直すと元のテキストに戻るはずです。切り出しの取りこぼしがあります。"
    )


def test_score_range_and_identity() -> None:
    assert impl.score("料金プラン", "料金プラン") is not None, (
        "score が未実装です。README 10.3 の TODO(2) を実装してください。"
    )
    assert impl.score("料金プラン", "料金プラン") == 1.0, "同一テキストのスコアは 1.0 です。"
    s = impl.score("料金プラン", "採用情報のページ")
    assert 0.0 <= s <= 1.0, "スコアは 0.0〜1.0 に収まるはずです。"
    assert impl.score("あ", "何かの文") == 0.0, "2-gram が作れないクエリは 0.0 を返します。"


def test_score_prefers_related_text() -> None:
    related = impl.score("無料トライアルの期間", "無料トライアルは 30 日間で")
    unrelated = impl.score("無料トライアルの期間", "ガントチャートと外部カレンダー連携")
    assert related is not None, "score が未実装です。README 10.3 の TODO(2) を実装してください。"
    assert related > unrelated, (
        "関連する文のスコアが無関係な文を上回りません。クエリ側 2-gram の一致割合を確認してください。"
    )


def test_retrieve_returns_topk_sorted() -> None:
    results = impl.retrieve("料金プラン", impl.DOCUMENTS, top_k=3)
    assert results, "retrieve が未実装です。README 10.3 の TODO(3) を実装してください。"
    assert len(results) == 3, "top_k 件を返すはずです。"
    scores = [s for s, _ in results]
    assert scores == sorted(scores, reverse=True), "結果はスコア降順で並べます。"


def test_retrieve_finds_relevant_chunk() -> None:
    results = impl.retrieve("無料トライアルの期間は？", impl.DOCUMENTS, top_k=1)
    assert results, "retrieve が未実装です。README 10.3 の TODO(3) を実装してください。"
    top_score, top_chunk = results[0]
    assert "30 日間" in top_chunk, (
        "「無料トライアルの期間は？」の最上位はベータ社のチャンクになるはずです。"
        "スコアリングか並べ替えを見直してください。"
    )
    assert top_score > 0.0
