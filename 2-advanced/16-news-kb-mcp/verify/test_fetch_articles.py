"""16.3 の合格判定: RSS 差分取得。fixture だけで動き、ネットワークも AWS も呼ばない。"""

from __future__ import annotations

import pathlib

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = (CHAPTER_DIR / "fixtures" / "whats_new.xml").read_text()


def _no_todo() -> None:
    source = (CHAPTER_DIR / "exercises" / "fetch_articles.py").read_text()
    assert "TODO" not in source, (
        "exercises/fetch_articles.py に TODO が残っています。README 16.3 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


def test_no_todo_left() -> None:
    _no_todo()


def test_key_is_year_month_slug() -> None:
    _no_todo()
    from fetch_articles import build_article, parse_feed

    items = parse_feed(FIXTURE, source="whats-new")
    art = build_article(items[1])
    assert art.key.startswith("news/2026/09/"), "key が news/YYYY/MM/ で始まっていません（16.3.1 TODO(1)）"
    assert art.key.endswith(".md"), "key の拡張子は .md です（16.3.1 TODO(1)）"
    assert "amazon-s3-vectors" in art.key, "slug にタイトル由来の語が入っていません（16.3.1 TODO(1)）"


def test_markdown_has_title_and_url() -> None:
    _no_todo()
    from fetch_articles import build_article, parse_feed

    art = build_article(parse_feed(FIXTURE, source="whats-new")[0])
    lines = art.markdown.splitlines()
    assert lines[0].startswith("# "), "markdown の 1 行目は `# <title>` です（16.3.1 TODO(2)）"
    assert any("出典: https://" in line for line in lines), "出典 URL の行がありません（16.3.1 TODO(2)）"


def test_metadata_has_filter_keys() -> None:
    _no_todo()
    from fetch_articles import build_article, parse_feed

    art = build_article(parse_feed(FIXTURE, source="whats-new")[2])
    assert set(art.metadata) == {"published_at", "category", "source", "url", "title"}, (
        "metadata のキーは published_at / category / source / url / title の 5 つです（16.3.1 TODO(3)）"
    )
    assert art.metadata["source"] == "whats-new"
    assert art.metadata["published_at"].startswith("2026-09-03"), "published_at は ISO 8601 です"


def test_seen_guids_are_skipped() -> None:
    _no_todo()
    from fetch_articles import parse_feed, select_new_articles

    items = parse_feed(FIXTURE, source="whats-new")
    arts = select_new_articles(items, seen_guids={"whats-new-0001"})
    assert [a.guid for a in arts] == ["whats-new-0002", "whats-new-0003"], (
        "処理済み GUID がスキップされていません（16.3.1 TODO(4)）"
    )


def test_duplicate_guid_in_same_run() -> None:
    _no_todo()
    from fetch_articles import parse_feed, select_new_articles

    items = parse_feed(FIXTURE, source="whats-new")
    arts = select_new_articles(items + items, seen_guids=set())
    assert len(arts) == 3, "同一実行内の重複 GUID が 1 件に抑えられていません（16.3.1 TODO(4)）"
