"""MCP サーバに接続し、ツール一覧の取得と実行だけを行う（編集不要。LLM なし）。"""

import pathlib
import sys

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands.tools.mcp import MCPClient

SERVER = pathlib.Path(__file__).parent / "exercises" / "server.py"

# サーバをサブプロセスとして起動する接続定義
client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    )
)

with client:
    tools = client.list_tools_sync()
    print("tools:", [t.tool_name for t in tools])

    result = client.call_tool_sync(
        tool_use_id="check-1", name="company_search", arguments={"name": "acme"}
    )
    print("result:", result["content"][0]["text"])
