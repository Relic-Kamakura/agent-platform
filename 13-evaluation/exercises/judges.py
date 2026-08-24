"""ハンズオン 13.3: ルールベースの判定関数群。

章直下に judges.py としてコピーし、TODO を実装する。
実装が終わったら TODO コメントは消す。完成形は solutions/judges.py。

各関数は失敗メッセージのリストを返す（空 = 合格）。bool でなくメッセージを
返すのは、FAIL の理由がそのまま run_eval.py のレポートに出るようにするため。
"""

from __future__ import annotations


def judge_contains(report: str, terms: list[str]) -> list[str]:
    """含むべき語。事実の取りこぼしを検出する。"""
    # この関数が型の見本。失敗した項目ごとにメッセージを 1 つ積む
    return [f"含むべき語が無い: {term!r}" for term in terms if term not in report]


def judge_not_contains(report: str, terms: list[str]) -> list[str]:
    """含んではいけない語。でっち上げ・禁止表現を検出する。"""
    # TODO(1): judge_contains と逆の条件で失敗メッセージのリストを返す
    ...


def judge_source(report: str) -> list[str]:
    """出典 URL の有無。出典の無い報告は検証できない。"""
    # TODO(2): report に http:// か https:// があれば合格（空リスト）。
    #   無ければ「出典 URL が 1 つも無い」の 1 件を返す
    ...


def judge_tool_calls(tool_calls: int, limit: int) -> list[str]:
    """ツール呼び出し数の上限。調査の暴走・非効率を検出する。"""
    # TODO(3): limit を超えていたら、実測値と上限の両方が読めるメッセージを 1 件返す
    ...


def judge_tokens(usage: dict, limit: int) -> list[str]:
    """トークン消費の上限。コスト退行を検出する。"""
    # TODO(4): usage の totalTokens（キーが無ければ 0）を limit と比較する。
    #   超えていたら実測値と上限が読めるメッセージを 1 件返す
    ...


def judge_case(report: str, usage: dict, tool_calls: int, expect: dict) -> list[str]:
    """1 ケース分の判定。expect に書かれたルールだけを適用する。"""
    # TODO(5): expect のキーに応じて上の判定を呼び分け、失敗を 1 つのリストに連結して返す。
    #   キーは contains / not_contains / require_source / max_tool_calls / max_total_tokens。
    #   書かれていないルールは適用しない
    ...
