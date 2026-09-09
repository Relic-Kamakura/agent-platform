"""Fetch Lambda（完成品・編集不要）: RSS を取得し、新着だけを S3 に置く。

ロジックの本体（parse_feed / select_new_articles）は exercises/fetch_articles.py と
同じ形。デプロイ用に、取得（urllib）と状態（DynamoDB）と保存（S3）をここで足している。
"""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC
from email.utils import parsedate_to_datetime

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FEEDS = {
    "whats-new": "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
    "news-blog": "https://aws.amazon.com/blogs/aws/feed/",
    "jp-blog": "https://aws.amazon.com/jp/blogs/news/feed/",
}

_ddb = boto3.resource("dynamodb")
_s3 = boto3.client("s3")


def slugify(title: str, max_chars: int = 60) -> str:
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:max_chars].rstrip("-") or "article"


def parse_feed(xml_text: str, source: str) -> list[dict]:
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


def handler(event, context):  # noqa: ANN001
    table = _ddb.Table(os.environ["STATE_TABLE"])
    bucket = os.environ["ARTICLE_BUCKET"]
    put = 0
    for source, url in FEEDS.items():
        req = urllib.request.Request(url, headers={"User-Agent": "handson-fetch/1.0"})
        with urllib.request.urlopen(req, timeout=20) as res:  # noqa: S310
            xml_text = res.read().decode("utf-8", errors="replace")
        for item in parse_feed(xml_text, source):
            if not item["guid"] or not item["published_at"]:
                continue
            if table.get_item(Key={"guid": item["guid"]}).get("Item"):
                continue
            year, month = item["published_at"][0:4], item["published_at"][5:7]
            key = f"news/{year}/{month}/{slugify(item['title'])}.md"
            markdown = f"# {item['title']}\n\n出典: {item['url']}\n\n{item['description']}\n"
            metadata = {
                "published_at": item["published_at"],
                "category": item["category"],
                "source": item["source"],
                "url": item["url"],
                "title": item["title"],
            }
            # metadata.json を先に置く。.md の ObjectCreated が SQS を起動する時点で
            # 両方揃っているようにするため
            _s3.put_object(
                Bucket=bucket,
                Key=f"{key}.metadata.json",
                Body=json.dumps({"metadataAttributes": metadata}, ensure_ascii=False).encode(),
            )
            _s3.put_object(Bucket=bucket, Key=key, Body=markdown.encode())
            table.put_item(Item={"guid": item["guid"], "key": key})
            put += 1
    logger.info(json.dumps({"message": "fetch_done", "new_articles": put}))
    return {"new_articles": put}
