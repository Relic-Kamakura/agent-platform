"""実エージェントに structured_output で判定させる（編集不要。Bedrock を呼ぶ）。"""

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

from strands import Agent
from strands.models import BedrockModel

from review import structured_verdict

# モデル ID。第1章 1.3 の手順で確認した、自分のリージョンで呼べる ID に合わせる
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

# 形式（判定の型と選択肢）はスキーマが強制するので、プロンプトは検証観点だけを教える
SYSTEM_PROMPT = """\
あなたはリサーチ報告の検証担当です。渡された報告を読み、以下だけを確認します。

1. 事実として書かれている記述に出典 URL が付いているか
2. 出典の内容から言えないことを断定していないか

報告そのものを書き直してはいけません。
"""

# 出典が無いまま断定している報告。revise 側の判定が期待される題材
REPORT = """\
A 社は 2025 年に国内シェア 1 位になった。
この市場は今後 10 年で 3 倍に成長することが確実である。
"""

# ツールを持たず、モデル呼び出しは 1 回だけの構成。
# ループが伸びる余地が無いため、第4章のような回数上限ガードは付けていない
agent = Agent(
    model=BedrockModel(
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        model_id=MODEL_ID,
        max_tokens=1024,
    ),
    system_prompt=SYSTEM_PROMPT,
    callback_handler=None,
)

if __name__ == "__main__":
    verdict = structured_verdict(agent, REPORT)
    print(f"verdict: {verdict.verdict}")
    for reason in verdict.reasons:
        print(f"- {reason}")
