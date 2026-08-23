"""AgentCore Runtime エントリポイント。

このファイルだけが AgentCore の HTTP 契約に触れる。
BedrockAgentCoreApp が POST /invocations と GET /ping を 0.0.0.0:8080 で提供する。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .agents.orchestrator import ResearchOrchestrator
from .config import get_settings
from .observability import log_event, new_request_id, set_request_id, setup_logging
from .streaming import stream_stages

app = BedrockAgentCoreApp()

_settings = get_settings()
setup_logging(_settings.log_level)
logger = logging.getLogger(__name__)

log_event(
    logger,
    logging.INFO,
    "startup",
    region=_settings.aws_region,
    inference_prefix=_settings.inference_prefix,
    search_provider=_settings.search_provider,
    auth_bypass=_settings.auth_bypass,
    **_settings.describe_models(),
)
if (warning := _settings.prefix_warning()) is not None:
    log_event(logger, logging.WARNING, "model_id_prefix_warning", detail=warning)

# Orchestrator はコールドスタート時に 1 度だけ構築する。
_orchestrator = ResearchOrchestrator(_settings)


@app.entrypoint
def invoke(payload: dict) -> dict | Iterator[dict]:
    """競合リサーチを 1 回実行する。

    payload:
        prompt: 調査依頼の文字列（必須）
        request_id: 呼び出し側が持つ追跡 ID（任意）
    """
    request_id = payload.get("request_id")
    if request_id:
        set_request_id(str(request_id))
    else:
        request_id = new_request_id()

    question = (payload.get("prompt") or "").strip()
    if not question:
        return {"error": "payload に 'prompt' が必要です。", "request_id": request_id}

    log_event(logger, logging.INFO, "invocation_started", question_length=len(question))

    # "stream": true ならジェネレータを返す。BedrockAgentCoreApp はジェネレータを
    # 受け取ると text/event-stream (SSE) で逐次送出する（実装をソースで確認済み）。
    # 進捗ステージ ("research"/"review"/"revise") がリアルタイムに届き、最後に結果が来る
    if payload.get("stream"):
        return stream_stages(
            lambda on_stage: {
                "request_id": request_id,
                **_orchestrator.run(question, on_stage=on_stage).to_payload(),
            }
        )

    result = _orchestrator.run(question)
    return {"request_id": request_id, **result.to_payload()}


if __name__ == "__main__":
    # BedrockAgentCoreApp.run() は host 省略時に 127.0.0.1 へ bind するため、
    # コンテナ契約 (0.0.0.0:8080) を満たすよう明示する。SERVER_PORT はローカル開発用の逃し先
    app.run(host=_settings.server_host, port=_settings.server_port)
