"""第15章の合格判定。サーバ起動からツール実行まで、プロトコル越しに検証する（LLM なし）。"""

from __future__ import annotations

import pathlib
import sys

import pytest

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
SERVER = CHAPTER_DIR / "exercises" / "server.py"


def test_no_todo_left() -> None:
    source = SERVER.read_text(encoding="utf-8")
    assert "TODO" not in source, (
        "exercises/server.py に TODO が残っています。README 15.3 に沿って実装し、"
        "終わったら TODO コメントを消してください。"
    )


@pytest.fixture(scope="module")
def mcp_client():
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
    assert "company_search" in names, (
        f"company_search ツールが公開されていません: {names}。"
        "README 15.3 の TODO(1) を実装してください。"
    )


def test_tool_docstring_travels_over_protocol(mcp_client) -> None:
    tools = {t.tool_name: t for t in mcp_client.list_tools_sync()}
    assert "company_search" in tools, (
        "company_search ツールが公開されていません。README 15.3 の TODO(1) を実装してください。"
    )
    spec = tools["company_search"].tool_spec
    description = str(spec.get("description", ""))
    assert "含まないもの" in description, (
        "docstring の 3 節（含まないもの）がプロトコル越しに届いていません。"
        "MCP でも docstring がそのままツール定義になります（README 15.3）。"
    )


def test_tool_call_over_protocol(mcp_client) -> None:
    result = mcp_client.call_tool_sync(
        tool_use_id="verify-1", name="company_search", arguments={"name": "ACME"}
    )
    text = result["content"][0]["text"]
    assert "49" in text, (
        f"company_search('ACME') が Acme の要約を返しません: {text!r}。"
        "大文字小文字を無視して _DATA を引いてください（README 15.3 の TODO(2)）。"
    )
