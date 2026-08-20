"""第14章の合格判定。サーバ起動からツール実行まで、プロトコル越しに検証する（LLM なし）。"""

from __future__ import annotations

import pathlib
import sys

import pytest

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
SERVER = CHAPTER_DIR / "01_mcp_server.py"


@pytest.fixture(scope="module")
def mcp_client():
    if not SERVER.exists():
        pytest.fail("01_mcp_server.py がありません。README の 14.2 に沿って書いてください。")
    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client
    from strands.tools.mcp import MCPClient

    client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command=sys.executable, args=[str(SERVER)], cwd=str(CHAPTER_DIR))
        )
    )
    with client:
        yield client


def test_server_exposes_company_search(mcp_client) -> None:
    names = [t.tool_name for t in mcp_client.list_tools_sync()]
    assert "company_search" in names, f"company_search ツールが公開されていません: {names}"


def test_tool_docstring_travels_over_protocol(mcp_client) -> None:
    tools = {t.tool_name: t for t in mcp_client.list_tools_sync()}
    spec = tools["company_search"].tool_spec
    description = str(spec.get("description", ""))
    assert "含まないもの" in description, (
        "docstring の 3 節（含まないもの）がプロトコル越しに届いていません。"
        "MCP でも docstring がそのままツール定義になります（14.2）。"
    )


def test_tool_call_over_protocol(mcp_client) -> None:
    result = mcp_client.call_tool_sync(
        tool_use_id="verify-1", name="company_search", arguments={"name": "ACME"}
    )
    text = result["content"][0]["text"]
    assert "49" in text, f"company_search('ACME') が Acme の要約を返しません: {text!r}"
