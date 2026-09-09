"""ハンズオン 16.4: Gateway ツール Lambda のロジック。

Gateway の Lambda ターゲットは、ツールの引数だけを event として渡し、
どのツールが呼ばれたかは context.client_context.custom["bedrockAgentCoreToolName"]
で渡してくる（ツール名には「ターゲット名___」の接頭辞が付く）。
このファイルは boto3 クライアントを引数で受け取る。AWS もネットワークも呼ばない
形でテストできる（第6章の技法）。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

DELIMITER = "___"


def build_retrieval_filter(
    since_days: int | None = None,
    category: str | None = None,
    source: str | None = None,
    now: datetime | None = None,
) -> dict | None:
    """Retrieve の metadata フィルタを組み立てる。

    条件が 0 件なら None、1 件ならその条件そのもの、
    2 件以上なら {"andAll": [...]} を返す。
    使う演算子: category / source は equals、since_days は
    published_at の greaterThanOrEquals（ISO 8601 文字列で比較する）。
    """
    now = now or datetime.now(UTC)
    conditions: list[dict] = []

    # TODO(1): category と source が指定されていたら
    #   {"equals": {"key": "<キー名>", "value": <値>}} を conditions に足す。
    #   since_days が指定されていたら now - timedelta(days=since_days) を ISO 8601 にして
    #   {"greaterThanOrEquals": {"key": "published_at", "value": <ISO 文字列>}} を足す。
    ...

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
    """KB を検索し、スコア・タイトル・URL・抜粋・published_at・s3_key を返す。

    深掘りは get_article の仕事なので、抜粋は 300 文字で切り詰める。
    """
    # TODO(2): retrieve_client.retrieve(...) を呼ぶ。
    #   - knowledgeBaseId と retrievalQuery={"text": query} を渡す
    #   - retrievalConfiguration={"vectorSearchConfiguration": {...}} に
    #     numberOfResults=5 と、build_retrieval_filter の結果が None でなければ
    #     "filter" を入れる（None のときは filter キー自体を入れない）
    #   応答の retrievalResults を、次のキーの辞書のリストにして返す:
    #     score / title / url / published_at / excerpt（content.text の先頭 300 文字）/
    #     s3_key（location.s3Location.uri の s3://<bucket>/ より後ろ）
    ...


def get_article(s3_client, article_bucket: str, s3_key: str) -> dict:
    """S3 から記事 Markdown の全文を返す。"""
    body = s3_client.get_object(Bucket=article_bucket, Key=s3_key)["Body"].read()
    return {"s3_key": s3_key, "markdown": body.decode("utf-8")}


def dispatch(event, context, retrieve_client, s3_client, knowledge_base_id: str, article_bucket: str) -> dict:
    """ツール名で処理を振り分ける。Gateway ターゲットの入口。"""
    # TODO(3): context.client_context.custom["bedrockAgentCoreToolName"] から
    #   ツール名を取り出し、「ターゲット名___」の接頭辞を取り除く。
    #   - "search_aws_updates" なら event の query / since_days / category / source を
    #     渡して search_aws_updates を呼び、{"results": [...]} を返す
    #   - "get_article" なら event の s3_key を渡して get_article の結果を返す
    #   - それ以外は {"error": f"unknown tool: {ツール名}"} を返す
    ...
