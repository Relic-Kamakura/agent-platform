"""ハンズオン 16.3: RSS の差分取得。

RSS フィードを解析し、処理済み GUID を除いた新着だけを
S3 に置く形（キーと本文と metadata）へ整形する。
このファイルはネットワークも AWS も呼ばない。取得と保存は
呼び出し側（Lambda ハンドラや実行スクリプト）が行う。
"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime


@dataclass(frozen=True)
class Article:
    """S3 に置く 1 記事分の成果物。"""

    guid: str
    key: str  # 例: news/2026/09/amazon-s3-vectors-is-now-available.md
    markdown: str
    metadata: dict


def slugify(title: str, max_chars: int = 60) -> str:
    """タイトルを S3 キーに使える slug にする。

    英数字以外をハイフンに置き換え、連続ハイフンを 1 つにまとめ、
    先頭末尾のハイフンを落とし、max_chars で切り詰める。全て小文字。
    """
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:max_chars].rstrip("-") or "article"


def parse_feed(xml_text: str, source: str) -> list[dict]:
    """RSS 2.0 の XML から item を辞書のリストにして返す。

    返す辞書のキー: guid / title / url / published_at（ISO 8601 文字列）/
    category / source / description。
    """
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iter("item"):
        published = item.findtext("pubDate") or ""
        published_at = parsedate_to_datetime(published).astimezone(UTC).isoformat() if published else ""
        items.append(
            {
                "guid": item.findtext("guid") or item.findtext("link") or "",
                "title": item.findtext("title") or "",
                "url": item.findtext("link") or "",
                "published_at": published_at,
                "category": item.findtext("category") or "",
                "source": source,
                "description": item.findtext("description") or "",
            }
        )
    return items


def build_article(item: dict) -> Article:
    """item 1 件を S3 に置く形へ整形する。

    - key は news/YYYY/MM/<slug>.md（YYYY/MM は published_at から取る）
    - markdown は 1 行目に `# <title>`、空行、出典 URL、空行、description
    - metadata は published_at / published_epoch / category / source / url / title の 6 キー
    """
    # TODO(1): published_at（ISO 8601）から年と月を取り出し、
    #   news/YYYY/MM/<slug>.md 形式の key を組み立てる（slug は slugify(title)）。
    #   月は 2 桁ゼロ埋め（9 月なら "09"）。
    key = ...

    # TODO(2): markdown を組み立てる。形式:
    #   # <title>
    #   （空行）
    #   出典: <url>
    #   （空行）
    #   <description>
    markdown = ...

    # TODO(3): metadata 辞書を組み立てる。キーは published_at / published_epoch /
    #   category / source / url / title の 6 つ。S3 には <key>.metadata.json として置かれ、
    #   Knowledge Base の検索フィルタの供給源になる。
    #   published_epoch は datetime.fromisoformat(published_at).timestamp() を int にした
    #   UNIX 秒。日付の絞り込みに使う greaterThanOrEquals は数値にしか効かないため、
    #   表示用の published_at（文字列）とは別にこの数値を持たせる。
    metadata = ...

    return Article(guid=item["guid"], key=key, markdown=markdown, metadata=metadata)


def select_new_articles(items: list[dict], seen_guids: set[str]) -> list[Article]:
    """処理済み GUID を除いた新着だけを Article にして返す。

    同一実行内の重複 GUID も 1 件に抑える（冪等性の一部）。
    """
    # TODO(4): seen_guids に無い item だけ build_article で整形して返す。
    #   このとき、この関数の中でも一度処理した GUID をスキップすること。
    ...
