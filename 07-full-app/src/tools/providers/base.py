"""検索プロバイダの共通インタフェース。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SearchResult:
    """検索結果 1 件。

    出典 URL を必須にしている。ReviewAgent が出典の有無を検証できるようにするため。
    """

    title: str
    url: str
    snippet: str

    def to_markdown(self) -> str:
        return f"- **{self.title}**\n  {self.snippet}\n  出典: {self.url}"


@runtime_checkable
class SearchProvider(Protocol):
    """Web 検索の実装。

    実装は失敗時に src.errors.SearchProviderError 系を送出すること。
    例外を握りつぶして空リストを返してはならない。
    「検索したが 0 件」と「検索自体が失敗」を呼び出し側が区別できなくなるため。
    """

    name: str

    def search(self, query: str, max_results: int) -> list[SearchResult]: ...
