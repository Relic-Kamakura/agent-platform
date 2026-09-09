"""コンテナ契約を確かめるための最小エージェント。LLM は呼ばず、payload をそのまま返す。

これをコンテナ化するのが第17章のハンズオン。Dockerfile は自分で書く。
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    return {"echo": payload.get("prompt", ""), "chapter": 17}


if __name__ == "__main__":
    # コンテナ契約は 0.0.0.0:8080。host を省略すると run() が実行環境を見て bind 先を決めるので、
    # 判定に任せず明示する
    app.run(host="0.0.0.0", port=8080)
