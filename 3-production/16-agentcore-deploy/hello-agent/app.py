"""コンテナ契約を確かめるための最小エージェント。LLM は呼ばず、payload をそのまま返す。

これをコンテナ化するのが第8章のハンズオン。Dockerfile は自分で書く。
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    return {"echo": payload.get("prompt", ""), "chapter": 8}


if __name__ == "__main__":
    # コンテナ契約: 0.0.0.0:8080。host を省略すると 127.0.0.1 に bind されて契約を満たさない
    app.run(host="0.0.0.0", port=8080)
