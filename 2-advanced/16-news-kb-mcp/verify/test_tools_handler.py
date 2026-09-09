"""16.4 の合格判定: Gateway ツール Lambda。boto3 は偽クライアントで差し替え、AWS を呼ばない。"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime
from types import SimpleNamespace

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
NOW = datetime(2026, 9, 10, tzinfo=UTC)


def _no_todo() -> None:
    source = (CHAPTER_DIR / "exercises" / "tools_handler.py").read_text()
    assert "TODO" not in source, (
        "exercises/tools_handler.py に TODO が残っています。README 16.4 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


class _FakeRetrieve:
    def __init__(self) -> None:
        self.kwargs: dict = {}

    def retrieve(self, **kwargs):
        self.kwargs = kwargs
        return {
            "retrievalResults": [
                {
                    "score": 0.71,
                    "content": {"text": "S3 Vectors expands regional availability." * 20},
                    "metadata": {
                        "title": "S3 Vectors in additional regions",
                        "url": "https://aws.amazon.com/x",
                        "published_at": "2026-09-02T09:30:00+00:00",
                    },
                    "location": {"s3Location": {"uri": "s3://articles/news/2026/09/s3-vectors.md"}},
                }
            ]
        }


class _FakeS3:
    def get_object(self, Bucket: str, Key: str):  # noqa: N803
        return {"Body": SimpleNamespace(read=lambda: f"# 記事\n\nbucket={Bucket} key={Key}\n".encode())}


def _context(tool: str):
    return SimpleNamespace(client_context=SimpleNamespace(custom={"bedrockAgentCoreToolName": tool}))


def test_no_todo_left() -> None:
    _no_todo()


def test_filter_none_when_no_conditions() -> None:
    _no_todo()
    from tools_handler import build_retrieval_filter

    assert build_retrieval_filter() is None, "条件が無ければ None を返します（16.4.1 TODO(1)）"


def test_filter_single_condition_is_bare() -> None:
    _no_todo()
    from tools_handler import build_retrieval_filter

    f = build_retrieval_filter(source="whats-new")
    assert f == {"equals": {"key": "source", "value": "whats-new"}}, (
        "条件 1 件のときは andAll で包みません（16.4.1 TODO(1)）"
    )


def test_filter_combines_with_and_all() -> None:
    _no_todo()
    from tools_handler import build_retrieval_filter

    f = build_retrieval_filter(since_days=7, category="Amazon S3", now=NOW)
    assert set(f) == {"andAll"} and len(f["andAll"]) == 2, "2 件以上は andAll で束ねます（16.4.1 TODO(1)）"
    ge = [c for c in f["andAll"] if "greaterThanOrEquals" in c][0]["greaterThanOrEquals"]
    assert ge["key"] == "published_at" and ge["value"].startswith("2026-09-03"), (
        "since_days は published_at の greaterThanOrEquals にします（16.4.1 TODO(1)）"
    )


def test_search_passes_filter_and_maps_results() -> None:
    _no_todo()
    from tools_handler import search_aws_updates

    fake = _FakeRetrieve()
    results = search_aws_updates(fake, "KB123", query="s3 vectors", source="whats-new")
    vs = fake.kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]
    assert fake.kwargs["knowledgeBaseId"] == "KB123"
    assert vs["numberOfResults"] == 5, "numberOfResults は 5 です（16.4.1 TODO(2)）"
    assert vs["filter"] == {"equals": {"key": "source", "value": "whats-new"}}
    assert results[0]["s3_key"] == "news/2026/09/s3-vectors.md", (
        "s3_key は s3://<bucket>/ より後ろです（16.4.1 TODO(2)）"
    )
    assert len(results[0]["excerpt"]) <= 300, "excerpt は 300 文字で切り詰めます（16.4.1 TODO(2)）"


def test_search_omits_filter_key_when_none() -> None:
    _no_todo()
    from tools_handler import search_aws_updates

    fake = _FakeRetrieve()
    search_aws_updates(fake, "KB123", query="anything")
    vs = fake.kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]
    assert "filter" not in vs, "フィルタ無しのときは filter キー自体を入れません（16.4.1 TODO(2)）"


def test_dispatch_strips_target_prefix() -> None:
    _no_todo()
    from tools_handler import dispatch

    out = dispatch(
        event={"query": "s3"},
        context=_context("news-tools___search_aws_updates"),
        retrieve_client=_FakeRetrieve(),
        s3_client=_FakeS3(),
        knowledge_base_id="KB123",
        article_bucket="articles",
    )
    assert "results" in out, "ターゲット名___ の接頭辞を取り除いて振り分けます（16.4.1 TODO(3)）"


def test_dispatch_get_article_and_unknown() -> None:
    _no_todo()
    from tools_handler import dispatch

    out = dispatch(
        event={"s3_key": "news/2026/09/a.md"},
        context=_context("news-tools___get_article"),
        retrieve_client=_FakeRetrieve(),
        s3_client=_FakeS3(),
        knowledge_base_id="KB123",
        article_bucket="articles",
    )
    assert out["markdown"].startswith("# "), "get_article は markdown 全文を返します（16.4.1 TODO(3)）"

    out = dispatch(
        event={},
        context=_context("news-tools___nope"),
        retrieve_client=_FakeRetrieve(),
        s3_client=_FakeS3(),
        knowledge_base_id="KB123",
        article_bucket="articles",
    )
    assert "error" in out, "未知のツール名は error を返します（16.4.1 TODO(3)）"
