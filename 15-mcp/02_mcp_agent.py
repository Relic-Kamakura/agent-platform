"""MCP サーバのツールをエージェントに渡し、モデルに選ばせて呼ぶ（編集不要。Bedrock を呼ぶ）。"""

import os
import pathlib
import sys

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

SERVER = pathlib.Path(__file__).parent / "exercises" / "server.py"

client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    )
)

with client:
    agent = Agent(
        model=BedrockModel(
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            model_id=os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"),
            max_tokens=512,
        ),
        system_prompt="社内データベースを使って質問に答えてください。",
        tools=client.list_tools_sync(),  # MCP のツールがそのまま tools になる
    )
    agent("Acme と Globex の価格を比較して")
