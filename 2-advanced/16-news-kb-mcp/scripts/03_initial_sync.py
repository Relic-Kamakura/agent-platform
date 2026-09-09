"""初回同期（実機・編集不要）: Fetch Lambda を 1 回起動し、取り込みジョブの完了を待つ。

    AWS_REGION=<リージョン> FETCH_FN=<関数名> KB_ID=<KB ID> DS_ID=<データソース ID> \
      uv run scripts/03_initial_sync.py
"""

import json
import os
import time

import boto3

region = os.environ["AWS_REGION"]
lam = boto3.client("lambda", region_name=region)
agent = boto3.client("bedrock-agent", region_name=region)

print("Fetch Lambda を起動します…")
res = lam.invoke(FunctionName=os.environ["FETCH_FN"])
print("fetch:", json.loads(res["Payload"].read()))

kb_id, ds_id = os.environ["KB_ID"], os.environ["DS_ID"]
print("取り込みジョブの状態を確認します（60 秒ごと・最大 15 分）…")
for _ in range(15):
    time.sleep(60)
    jobs = agent.list_ingestion_jobs(knowledgeBaseId=kb_id, dataSourceId=ds_id, maxResults=1)
    summaries = jobs.get("ingestionJobSummaries", [])
    if not summaries:
        print("  ジョブ未開始（SQS のバッチ待ちの可能性）")
        continue
    status = summaries[0]["status"]
    print(f"  status={status}")
    if status == "COMPLETE":
        stats = summaries[0].get("statistics", {})
        print("完了:", json.dumps(stats, default=str))
        break
