"""ストリーミング橋渡し (stream_stages) の検証。LLM は呼ばない。"""

from __future__ import annotations

from src.streaming import stream_stages


def test_stages_then_result_in_order() -> None:
    def work(on_stage):
        on_stage("research")
        on_stage("review")
        return {"request_id": "r1", "report": "done"}

    events = list(stream_stages(work))
    assert [e.get("stage") for e in events[:2]] == ["research", "review"]
    assert events[-1] == {"event": "result", "request_id": "r1", "report": "done"}


def test_error_is_delivered_as_event() -> None:
    def work(on_stage):
        on_stage("research")
        raise RuntimeError("boom")

    events = list(stream_stages(work))
    assert events[0] == {"event": "stage", "stage": "research"}
    assert events[-1]["event"] == "error"
    assert "boom" in events[-1]["detail"]
