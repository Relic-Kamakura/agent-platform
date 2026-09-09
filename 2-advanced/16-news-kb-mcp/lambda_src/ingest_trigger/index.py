"""Ingest Trigger Lambda（完成品・編集不要）: SQS バッチを受けて StartIngestionJob を 1 回呼ぶ。

KB あたり同時 1 ジョブの制約があるため、実行中のジョブがあれば新たに開始せず、
バッチ全件を「失敗」として返して SQS の再配信（可視性タイムアウト）に任せる。
"""

from __future__ import annotations

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_client = boto3.client("bedrock-agent")

RUNNING_STATUSES = {"STARTING", "IN_PROGRESS"}


def handler(event, context):  # noqa: ANN001
    kb_id = os.environ["KNOWLEDGE_BASE_ID"]
    ds_id = os.environ["DATA_SOURCE_ID"]
    records = event.get("Records", [])

    jobs = _client.list_ingestion_jobs(knowledgeBaseId=kb_id, dataSourceId=ds_id, maxResults=5)
    running = [j for j in jobs.get("ingestionJobSummaries", []) if j.get("status") in RUNNING_STATUSES]
    if running:
        logger.info(json.dumps({"message": "ingestion_running", "requeue": len(records)}))
        return {"batchItemFailures": [{"itemIdentifier": r["messageId"]} for r in records]}

    job = _client.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
    logger.info(
        json.dumps(
            {
                "message": "ingestion_started",
                "job_id": job["ingestionJob"]["ingestionJobId"],
                "batch_size": len(records),
            }
        )
    )
    return {"batchItemFailures": []}
