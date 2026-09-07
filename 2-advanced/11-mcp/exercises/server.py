"""ハンズオン 15.3: 検索ツールを提供する MCP サーバ。stdio で起動される。

TODO を実装し、`uv run 01_list_tools.py` で動かす。
実装が終わったら TODO コメントは消す。完成形は solutions/server.py。
"""

from mcp.server.fastmcp import FastMCP

# サーバ名はクライアント側のログに出る識別子
mcp = FastMCP("search-server")

# 固定データ。実運用ならここが社内 API や DB への問い合わせになる
_DATA = {
    "acme": "Acme Analytics: Starter 月額 49 ドル / Business 149 ドル。SSO は Enterprise のみ。",
    "globex": "Globex Insights: Pro 月額 99 ドル。SSO は全プラン対応。異常検知機能あり。",
}


# TODO(1): @mcp.tool() を付けた company_search(name: str) -> str を定義する。
#   docstring は第3章の 3 節構成（受け取るもの / 返すもの / 含まないもの）で書く。
#   MCP ではこの docstring がそのままツール定義としてクライアントへ渡る。
#   - 受け取るもの: name は "acme" か "globex"。大文字小文字は無視すること
#   - 返すもの: その企業の要約 1 行。見つからなければ「該当なし: {name}」
#   - 含まないもの: Web 検索。ここにあるのは社内データだけ
# TODO(2): 関数本体を実装する。_DATA を name の小文字化で引く。


if __name__ == "__main__":
    mcp.run()  # stdio で待ち受ける
