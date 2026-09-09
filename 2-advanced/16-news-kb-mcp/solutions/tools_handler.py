"""第16章の模範解答: Gateway ツール Lambda のロジック（exercises/tools_handler.py の完成形）。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

DELIMITER = "___"


def build_retrieval_filter(
    since_days: int | None = None,
    category: str | None = None,
    source: str | None = None,
    now: datetime | None = None,
) -> dict | None:
    """Retrieve の metadata フィルタを組み立てる。"""
    now = now or datetime.now(UTC)
    conditions: list[dict] = []
    if category:
        conditions.append({"equals": {"key": "category", "value": category}})
    if source:
        conditions.append({"equals": {"key": "source", "value": source}})
    if since_days:
        # greaterThanOrEquals は数値にしか効かないので、UNIX 秒で比較する
        since = int((now - timedelta(days=since_days)).timestamp())
        conditions.append({"greaterThanOrEquals": {"key": "published_epoch", "value": since}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"andAll": conditions}


def search_aws_updates(
    retrieve_client,
    knowledge_base_id: str,
    query: str,
    since_days: int | None = None,
    category: str | None = None,
    source: str | None = None,
) -> list[dict]:
    """KB を検索し、スコア・タイトル・URL・抜粋・published_at・s3_key を返す。"""
    vector_config: dict = {"numberOfResults": 5}
    retrieval_filter = build_retrieval_filter(since_days=since_days, category=category, source=source)
    if retrieval_filter is not None:
        vector_config["filter"] = retrieval_filter

    response = retrieve_client.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": vector_config},
    )

    results = []
    for hit in response.get("retrievalResults", []):
        metadata = hit.get("metadata", {})
        uri = hit.get("location", {}).get("s3Location", {}).get("uri", "")
        s3_key = uri.split("/", 3)[3] if uri.startswith("s3://") and uri.count("/") >= 3 else uri
        results.append(
            {
                "score": hit.get("score"),
                "title": metadata.get("title", ""),
                "url": metadata.get("url", ""),
                "published_at": metadata.get("published_at", ""),
                "excerpt": hit.get("content", {}).get("text", "")[:300],
                "s3_key": s3_key,
            }
        )
    return results


def get_article(s3_client, article_bucket: str, s3_key: str) -> dict:
    """S3 から記事 Markdown の全文を返す。"""
    body = s3_client.get_object(Bucket=article_bucket, Key=s3_key)["Body"].read()
    return {"s3_key": s3_key, "markdown": body.decode("utf-8")}


def dispatch(event, context, retrieve_client, s3_client, knowledge_base_id: str, article_bucket: str) -> dict:
    """ツール名で処理を振り分ける。Gateway ターゲットの入口。"""
    raw_name = context.client_context.custom["bedrockAgentCoreToolName"]
    tool_name = raw_name.split(DELIMITER, 1)[-1]

    if tool_name == "search_aws_updates":
        results = search_aws_updates(
            retrieve_client,
            knowledge_base_id,
            query=event["query"],
            since_days=event.get("since_days"),
            category=event.get("category"),
            source=event.get("source"),
        )
        return {"results": results}
    if tool_name == "get_article":
        return get_article(s3_client, article_bucket, s3_key=event["s3_key"])
    return {"error": f"unknown tool: {tool_name}"}
