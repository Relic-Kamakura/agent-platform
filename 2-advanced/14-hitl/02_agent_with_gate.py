"""ApprovalGate を実エージェントに付けて、承認を求められる様子を観察する（編集不要。Bedrock を呼ぶ）。"""

import os
import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent, HookRegistry
from strands.models import BedrockModel

from approval_gate import ApprovalGate

# モデル ID。第1章 1.3 の手順で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """メールを送信する。

    受け取るもの: to（宛先アドレス）、subject（件名）、body（本文）。
    返すもの: 送信結果のメッセージ。
    含まないもの: 宛先の検証。アドレスの実在は確認しない。
    """
    # 演習用の疑似送信。実際にメールは飛ばない
    return f"{to} に送信しました（件名: {subject}）"


@dataclass
class ToolCallLimiter:
    """ツール呼び出し回数の上限。承認ゲートとは別の、暴走を止める側のガード（第4章）。"""

    max_calls: int
    _calls: int = field(default=0, init=False)

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(BeforeToolCallEvent, self._count)

    def _count(self, event: BeforeToolCallEvent) -> None:
        self._calls += 1
        if self._calls > self.max_calls:
            event.cancel_tool = (
                f"ツール呼び出しが上限 ({self.max_calls} 回) に達しました。"
                "ここまでの情報で結論をまとめてください。"
            )


def cli_approver(tool_name: str, tool_input: dict) -> bool:
    """人間に聞く approver。input() は同期なのでローカル実行専用。"""
    print(f"\nエージェントが {tool_name} を実行しようとしています: {tool_input}")
    return input("承認しますか？ [y/N]: ").strip().lower() == "y"


agent = Agent(
    model=BedrockModel(
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        model_id=MODEL_ID,
        max_tokens=1024,
    ),
    system_prompt="依頼に日本語で応えてください。メールの送信には send_email を使ってください。",
    tools=[send_email],
    hooks=[
        ToolCallLimiter(max_calls=3),
        ApprovalGate(requires_approval={"send_email"}, approver=cli_approver),
    ],
)

if __name__ == "__main__":
    agent("taro@example.com へ、明日の定例を 30 分後ろ倒しにしたい旨のメールを送って")
