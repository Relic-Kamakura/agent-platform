"""Gateway から届く形の event / context を手で作り、ツール Lambda のロジックに渡す
（編集不要。オフラインで動く）。

    uv run 02_tools_dry_run.py
"""

import json
import pathlib
import sys
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from tools_handler import dispatch  # noqa: E402


class FakeRetrieve:
    def retrieve(self, **kwargs):
        print("retrieve に渡った vectorSearchConfiguration:")
        print(" ", json.dumps(kwargs["retrievalConfiguration"]["vectorSearchConfiguration"], ensure_ascii=False))
        return {
            "retrievalResults": [
                {
                    "score": 0.71,
                    "content": {"text": "S3 Vectors expands regional availability."},
                    "metadata": {
                        "title": "S3 Vectors in additional regions",
                        "url": "https://aws.amazon.com/about-aws/whats-new/2026/09/s3-vectors-regions/",
                        "published_at": "2026-09-02T09:30:00+00:00",
                    },
                    "location": {"s3Location": {"uri": "s3://articles/news/2026/09/s3-vectors.md"}},
                }
            ]
        }


class FakeS3:
    def get_object(self, Bucket, Key):  # noqa: N803
        return {"Body": SimpleNamespace(read=lambda: b"# S3 Vectors in additional regions\n...")}


def context(tool_name: str):
    return SimpleNamespace(client_context=SimpleNamespace(custom={"bedrockAgentCoreToolName": tool_name}))


print("=== search_aws_updates（source=whats-new, since_days=7）===")
out = dispatch(
    event={"query": "S3 Vectors のリージョン", "source": "whats-new", "since_days": 7},
    context=context("news-tools___search_aws_updates"),
    retrieve_client=FakeRetrieve(),
    s3_client=FakeS3(),
    knowledge_base_id="KB_DUMMY",
    article_bucket="articles",
)
print(json.dumps(out, ensure_ascii=False, indent=2))

print("\n=== get_article ===")
out = dispatch(
    event={"s3_key": "news/2026/09/s3-vectors.md"},
    context=context("news-tools___get_article"),
    retrieve_client=FakeRetrieve(),
    s3_client=FakeS3(),
    knowledge_base_id="KB_DUMMY",
    article_bucket="articles",
)
print(json.dumps(out, ensure_ascii=False, indent=2))
