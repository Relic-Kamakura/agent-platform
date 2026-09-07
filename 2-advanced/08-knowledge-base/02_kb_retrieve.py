"""Bedrock Knowledge Bases の Retrieve API を直接呼ぶ（編集不要。AWS を呼ぶ）。"""

import os

import boto3

client = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)

response = client.retrieve(
    knowledgeBaseId=os.environ["KB_ID"],
    retrievalQuery={"text": "無料トライアルの期間は？"},
    retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}},
)

for result in response["retrievalResults"]:
    print(f"{result['score']:.3f} | {result['content']['text'][:60]}")
