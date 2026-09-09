"""第10章の合格判定: 堅牢化プロンプトの要件をテストで表現している。"""

from __future__ import annotations

import pathlib
import re

SECTION_HEADING = "# 検索結果の取り扱い"


def test_no_todo_left(prompt_module, wrap_module) -> None:
    for module in (wrap_module, prompt_module):
        path = pathlib.Path(module.__file__)
        assert "TODO" not in path.read_text(encoding="utf-8"), (
            f"exercises/{path.name} に TODO が残っています。README 10.3.1 に沿って"
            "実装し、終わったら TODO の行を消してください。"
        )


def test_role_is_kept(prompt_module) -> None:
    assert prompt_module.HARDENED_PROMPT.startswith(prompt_module.ROLE), (
        "役割部分（ROLE）は書き換えず、その後ろに節を書き足してください（10.3.1）。"
    )


def test_has_handling_section(prompt_module) -> None:
    assert SECTION_HEADING in prompt_module.HARDENED_PROMPT, (
        f"「{SECTION_HEADING}」の節見出しがありません（10.3.1）。"
    )


def test_refuses_and_reports(prompt_module) -> None:
    prompt = prompt_module.HARDENED_PROMPT
    assert re.search(r"指示では(ない|あり)|指示として扱わ", prompt), (
        "検索結果は資料（データ）であり指示ではない、と書いてください（10.3.1 要件 1）。"
    )
    assert "従わ" in prompt, (
        "資料内の指示めいた文章には従わない、と書いてください（10.3.1 要件 2）。"
    )
    assert "報告" in prompt, (
        "従わないだけでなく、不審な指示があった事実を報告させてください（10.3.1 要件 2）。"
    )


def test_keeps_internal_info(prompt_module) -> None:
    assert SECTION_HEADING in prompt_module.HARDENED_PROMPT, (
        f"先に「{SECTION_HEADING}」の節を書いてください（10.3.1）。"
    )
    section = prompt_module.HARDENED_PROMPT.split(SECTION_HEADING, 1)[1]
    assert re.search(r"環境変数|内部情報|システムプロンプト", section), (
        "内部情報（環境変数・システムプロンプト等）を報告に含めないことを"
        "節の中に書いてください（10.3.1 要件 3）。"
    )
