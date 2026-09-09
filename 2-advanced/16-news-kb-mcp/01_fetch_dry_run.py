"""fixture の RSS を差分取得に通して、S3 に置かれる形を表示する（編集不要。オフラインで動く）。

    uv run 01_fetch_dry_run.py
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from fetch_articles import parse_feed, select_new_articles  # noqa: E402

fixture = (pathlib.Path(__file__).parent / "fixtures" / "whats_new.xml").read_text()
items = parse_feed(fixture, source="whats-new")

print(f"フィード内の記事: {len(items)} 件")
articles = select_new_articles(items, seen_guids={"whats-new-0001"})
print(f"GUID 1 件を処理済みとした場合の新着: {len(articles)} 件\n")

for art in articles:
    print(f"S3 キー   : {art.key}")
    print(f"metadata  : {json.dumps(art.metadata, ensure_ascii=False)}")
    print(f"markdown  : {art.markdown.splitlines()[0]} ...")
    print()
