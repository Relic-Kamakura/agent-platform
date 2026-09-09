"""Gateway ツール Lambda のエントリポイント（完成品・編集不要）。

ロジックは同じディレクトリの tools_handler.py（ハンズオンで実装したものを
cp してくる。README 16.4 参照）に置き、ここは環境変数と boto3 の接続だけを持つ。
"""

from __future__ import annotations

import os

import boto3

from tools_handler import dispatch

_runtime = boto3.client("bedrock-agent-runtime")
_s3 = boto3.client("s3")


def handler(event, context):  # noqa: ANN001
    return dispatch(
        event=event,
        context=context,
        retrieve_client=_runtime,
        s3_client=_s3,
        knowledge_base_id=os.environ["KNOWLEDGE_BASE_ID"],
        article_bucket=os.environ["ARTICLE_BUCKET"],
    )
