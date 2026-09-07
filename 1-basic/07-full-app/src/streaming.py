"""ストリーミング応答の橋渡し。

BedrockAgentCoreApp はエントリポイントがジェネレータを返すと
text/event-stream (SSE) で逐次送出する（実装をソースで確認済み）。
このモジュールは「別スレッドで実行しながら進捗を流す」変換だけを担い、
import 時の副作用を持たない（テストしやすさのため main.py から分離している）。
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from queue import Queue

_DONE = object()


def stream_stages(work: Callable[[Callable[[str], None]], dict]) -> Iterator[dict]:
    """work を別スレッドで実行し、ステージ通知と最終結果を順に yield する。

    work は on_stage コールバックを受け取り、最終結果の dict を返す関数。
    ジェネレータを消費するのは HTTP レスポンス側なので、work をスレッドへ逃がして
    「実行しながら流す」を成立させている。
    """
    queue: Queue = Queue()

    def _run() -> None:
        try:
            result = work(lambda stage: queue.put({"event": "stage", "stage": stage}))
            queue.put({"event": "result", **result})
        except Exception as exc:
            # スレッド境界。ここで拾わないと呼び出し側にエラーが届かない
            queue.put({"event": "error", "detail": str(exc)})
        finally:
            queue.put(_DONE)

    threading.Thread(target=_run, daemon=True).start()
    while (item := queue.get()) is not _DONE:
        yield item
