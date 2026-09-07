"""例外定義とエラー整形。

方針:
- ツール実行の失敗は例外を握りつぶさず、エージェントが次の判断をできる文字列に整形して返す。
- 「retryable かどうか」を型で表現する。エージェントに再試行の可否を伝えるため。
"""

from __future__ import annotations


class AgentPlatformError(Exception):
    """このリポジトリが送出する全例外の基底。"""


class ConfigurationError(AgentPlatformError):
    """設定が不正。起動時に検出して即座に落とすためのもの。"""


class ToolError(AgentPlatformError):
    """ツール実行中の失敗。

    Attributes:
        retryable: エージェントが同じ引数で再試行して意味があるか。
        hint: エージェントが次に取るべき行動。tool_result に含めてモデルに読ませる。
    """

    retryable: bool = False
    hint: str = ""

    def __init__(self, message: str, *, hint: str = "") -> None:
        super().__init__(message)
        if hint:
            self.hint = hint


class SearchProviderError(ToolError):
    """検索プロバイダが応答したが結果を返せなかった。"""

    retryable = False
    hint = "別のキーワードで検索し直すか、この観点は情報なしとして報告してください。"


class SearchProviderTimeout(SearchProviderError):
    """検索プロバイダがタイムアウトした。リトライ済みで、なお失敗している。"""

    retryable = True
    hint = "一時的な失敗の可能性があります。1 度だけ再試行し、それでも失敗したら情報なしとして報告してください。"


class SearchProviderRateLimited(SearchProviderError):
    """検索プロバイダにレート制限された。"""

    retryable = False
    hint = "これ以上検索できません。すでに取得済みの情報だけで報告をまとめてください。"


class SearchProviderNotConfigured(SearchProviderError):
    """プロバイダに必要な設定（API キーなど）が無い。"""

    retryable = False
    hint = "設定の問題であり、再試行しても解決しません。検索は行えないと報告してください。"


class ToolCallLimitExceeded(AgentPlatformError):
    """ツール呼び出し回数の上限に達した。コスト暴走を止めるための機構。"""


class TurnLimitExceeded(AgentPlatformError):
    """エージェントのターン数（モデル呼び出し回数）上限に達した。"""


def format_tool_error(exc: ToolError) -> str:
    """ツール例外を、モデルが読んで次の判断ができる形に整形する。

    握りつぶさずに「失敗した事実」「再試行の可否」「次に取るべき行動」を必ず含める。
    """
    parts = [f"ERROR[{type(exc).__name__}]: {exc}"]
    parts.append(f"retryable: {'yes' if exc.retryable else 'no'}")
    if exc.hint:
        parts.append(f"next_action: {exc.hint}")
    return "\n".join(parts)
