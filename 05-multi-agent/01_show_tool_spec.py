"""専門エージェントを包んだツールの tool_spec を表示する（編集不要。モデルは呼ばない）。"""

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "exercises"))

# BedrockModel はコンストラクタで boto3 クライアントを作る（ネットワークアクセスは無い。
# docs/troubleshooting.md 参照）。認証情報が未設定の環境でも動くよう、無い場合だけダミーを入れる
os.environ.setdefault("AWS_ACCESS_KEY_ID", "dummy")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "dummy")

from specialist import build_specialist_tool

tool = build_specialist_tool()

# オーケストレータのモデルに渡るのはこの JSON だけ。
# 中でエージェントが動いていることは、どこにも書かれていない
print(json.dumps(tool.tool_spec, ensure_ascii=False, indent=2))
