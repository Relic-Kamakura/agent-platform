"""検索ツールを提供する MCP サーバ。stdio で起動される。"""

from mcp.server.fastmcp import FastMCP

# サーバ名はクライアント側のログに出る識別子
mcp = FastMCP("search-server")

# 固定データ。実運用ならここが社内 API や DB への問い合わせになる
_DATA = {
    "acme": "Acme Analytics: Starter 月額 49 ドル / Business 149 ドル。SSO は Enterprise のみ。",
    "globex": "Globex Insights: Pro 月額 99 ドル。SSO は全プラン対応。異常検知機能あり。",
}


@mcp.tool()
def company_search(name: str) -> str:
    """企業名で社内データベースを検索し、要約を返す。

    受け取るもの:
        name: 企業名。"acme" または "globex"（大文字小文字は無視）。
    返すもの:
        その企業の要約 1 行。見つからなければ「該当なし」。
    含まないもの:
        Web 検索。ここにあるのは社内データだけ。
    """
    return _DATA.get(name.lower(), f"該当なし: {name}")


if __name__ == "__main__":
    mcp.run()  # stdio で待ち受ける
