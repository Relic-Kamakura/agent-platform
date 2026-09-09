"""第16章の模範解答: RSS の差分取得（exercises/fetch_articles.py の完成形）。"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC
from email.utils import parsedate_to_datetime


@dataclass(frozen=True)
class Article:
    """S3 に置く 1 記事分の成果物。"""

    guid: str
    key: str
    markdown: str
    metadata: dict


def slugify(title: str, max_chars: int = 60) -> str:
    """タイトルを S3 キーに使える slug にする。"""
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:max_chars].rstrip("-") or "article"


def parse_feed(xml_text: str, source: str) -> list[dict]:
    """RSS 2.0 の XML から item を辞書のリストにして返す。"""
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
    """item 1 件を S3 に置く形へ整形する。"""
    year = item["published_at"][0:4]
    month = item["published_at"][5:7]
    key = f"news/{year}/{month}/{slugify(item['title'])}.md"

    markdown = f"# {item['title']}\n\n出典: {item['url']}\n\n{item['description']}\n"

    metadata = {
        "published_at": item["published_at"],
        "category": item["category"],
        "source": item["source"],
        "url": item["url"],
        "title": item["title"],
    }
    return Article(guid=item["guid"], key=key, markdown=markdown, metadata=metadata)


def select_new_articles(items: list[dict], seen_guids: set[str]) -> list[Article]:
    """処理済み GUID を除いた新着だけを Article にして返す。"""
    articles: list[Article] = []
    done = set(seen_guids)
    for item in items:
        if item["guid"] in done:
            continue
        done.add(item["guid"])
        articles.append(build_article(item))
    return articles
