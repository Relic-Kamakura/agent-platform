# 第6章 エージェントのテスト

この章を終えると、自分のツールに CI で実行できるテストを書けるようになります。
テスト対象は `target/` に同梱した 2 つのモジュールで、雛形 1 本を手がかりに残り 7 本を書くところまでが課題です。

この章は独立した uv プロジェクトです。
最初に依存を入れてください。

```bash
cd 1-basic/06-agent-testing
uv sync
```

書くのは `exercises/test_fetch_page.py` だけで、完成形は `solutions/` にあります。
モデルも実ネットワークも呼びません。

## 6.1 概要

### 6.1.1 エージェントのテストの難しさ

モデルの応答は確率的で、同じ入力に同じ出力が返る保証がありません。
「期待値と一致すること」を前提とする assert は、モデルの出力に対しては書けません。
これがエージェントのテストが普通のコードと違う点です。

### 6.1.2 テストできる部分とできない部分

エージェントのコードには 2 種類の性質が同居しています。
テスト戦略はここで分かれます。

決定的なのは、設定の解決、ガードの発動、ツールの異常系、エージェント同士の呼び出しです。
普通の pytest で固定でき、この章で扱います。
確率的なのはモデルが良い報告を書けるかで、assert では検証できません。
こちらは評価（evals）の領分です。

決定的な部分は、プロンプトをどれだけ書き換えても変わってはいけない不変条件です。
それを普通のテストで固定し、確率的な部分だけを評価で測ります。
この分離が、エージェントを CI に載せるための前提です。

## 6.2 実装のポイント

### 6.2.1 外部 API のモック

`httpx.Client` を偽クラスに差し替えれば、timeout も 403 も 5xx も再現できます。
リトライ回数まで assert します（初回 + 2 回 = ちょうど 3 回で打ち切る）。
`time.sleep` も差し替えるので、指数バックオフのテストでも待ち時間はゼロです。

逆に、モデル応答をモックしてそのモックの中身を assert するテストは書かないでください。
自分の書いたモックを検証しているだけなので、カバレッジは増えますが、実装にバグを入れてもこのテストが落ちることはありません。
モックするのは外部 API で、assert するのは自分のコードの振る舞いです。

### 6.2.2 Agent の応答を受け取る境界

モデルの出力そのものは assert できませんが、その出力を受け取ってから後の処理は決定的なので assert できます。
境界に `AgentResult` を手で組んで渡せば、モデルは要りません。

```python
result = AgentResult(
    stop_reason="end_turn",
    message={"role": "assistant", "content": [{"text": "VERDICT: ok\n指摘なし"}]},
    metrics=EventLoopMetrics(),
    state={},
)
```

この境界には間違えやすい点があります。
`str(result.message)` は Python の dict 表現（`{'role': 'assistant', ...}`）を返すので、本文ではありません。
本文は `str(result)` で、`AgentResult.__str__` がテキストブロックを連結します。
`target/verdict.py` の `parse_verdict` はこの本文から判定行を読みます。
同じ形のテストが `1-basic/07-full-app/tests/test_agents.py` にあるので、あとで読み比べてください。

### 6.2.3 hook のコールバック直接呼び出し

ガードのテストにエージェントを動かす必要はありません。
イベントオブジェクトを手で作ってコールバックに渡せば、ループを実行せずに全分岐を検証できます。

### 6.2.4 仕様書としてのテスト

各章の verify/ は、要求仕様をテストで書いたものです。
「タイムアウトは 2 回リトライし、だめなら ERROR 形式で返す」をテストにしておけば、プロンプトを頻繁に書き換える時期でも、決定的な部分が変わっていないことを毎回数秒で確認できます。

## 6.3 ハンズオン: ツールにテストを書く

テスト対象は `target/fetch_page.py`（URL を受け取り本文を返すツール）と`target/verdict.py`（Agent の応答から判定を読む関数）です。
どちらも編集不要です。

要件は 3 つです。

1. テスト関数を 8 つ以上
2. 次の観点を含める
   - 正常系: 本文が返り、max_chars で切り詰められること
   - 異常系: 失敗時に `ERROR[` 形式で返ること（httpx をモックして再現する）
   - リトライ: 試行回数が設定どおりであること（`time.sleep` も差し替える）
   - URL 検証: http/https 以外を渡したとき、ネットワークを呼ばずに `ERROR[` が返ること
   - 4xx と 5xx の区別: 4xx は 1 回で打ち切り、5xx はリトライすること
   - Agent の応答を受け取る境界: `AgentResult` を手で組んで `parse_verdict` に渡すこと
3. LLM も実ネットワークも呼ばない

### 6.3.1 TODO を 6 個埋める

`exercises/test_fetch_page.py` を開いてください。
モック部品（`_Response` と `_client`）、`AgentResult` を組む `_agent_result`、正常系のテスト 1 本は書いてあり、TODO が 6 つ残っています。

1. URL 検証。`ftp://` などを渡し、httpx をモックせずに `ERROR[` 形式が返ることを assert する
2. 4xx。404 を返すモックで、`ERROR[` 形式と試行が 1 回で止まることを assert する
3. リトライ回数。タイムアウトを起こし続け、「初回 + リトライ 2 回 = 3 回」を assert する
4. 5xx。503 を 2 回返したあと 200 を返すモックで、本文が返ることを assert する
5. Agent の応答を受け取る境界。`parse_verdict` が本文から `"ok"` を読むことと、`str(result.message)` が本文ではないことを assert する
6. `target/fetch_page.py` を読み、上記でテストされていない分岐を 2 つ見つけてテストを書く

`@tool` でラップされた関数は `.__wrapped__` でラップ前の元の関数を取り出せます（雛形の `_tool()` がやっています）。
各テストに「このテストが落ちるのはどんなバグが入ったときか」を 1 行コメントで書くと、意図が後から読めます。

### 6.3.2 実行する

書けたら TODO コメントを消し、まず自分のテストを直接実行します。

```bash
uv run pytest exercises/test_fetch_page.py -q
```

書いた本数ぶんの passed が、1 秒未満で出るはずです。

```
........                                                                 [100%]
8 passed in 0.37s
```

実ネットワークを呼んでいたら、この速度にはなりません。

<details>
<summary>解答例</summary>

```python
def test_timeout_retries_then_reports(monkeypatch: pytest.MonkeyPatch) -> None:
    # 落ちるとき: リトライ回数が設定と乖離する、または例外を捕まえて何も返さないバグ
    calls = {"n": 0}

    def _raise():
        calls["n"] += 1
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "Client", _client(_raise))
    monkeypatch.setattr("time.sleep", lambda _s: None)

    out = _tool()(url="https://example.com")
    assert out.startswith("ERROR[")
    assert calls["n"] == 3  # 初回 + リトライ 2 回
    assert "retryable" in out


def test_verdict_is_read_from_body_not_message_repr() -> None:
    # 落ちるとき: str(result.message)（dict の文字列表現）から判定を読もうとするバグ
    result = _agent_result("VERDICT: ok\n指摘なし")
    assert parse_verdict(result) == "ok"
    assert str(result.message).startswith("{'role'")
```

全 8 本は `solutions/test_fetch_page.py` にあります。

</details>

### 6.3.3 合格判定

```bash
uv run pytest -q
```

`6 passed` で合格です。
テスト関数の数、httpx のモック使用、`parse_verdict` を呼ぶテストの有無を検査したうえで、あなたのテストをサブプロセスで実行し、全部通ることまで確認します。
verify が見るのは本数と手法だけで、何を assert しているかまでは判定しません。

## 6.4 まとめ

エージェントのテストでは、モデル出力そのものを assert しません。
決定的な部分（設定、ガード、ツール、Agent の応答を受け取る境界）を普通の pytest で固定し、確率的な部分は評価で測ります。
プロンプトは書き換えていくものですが、ガードとツールと呼び出しの繋がりはプロンプトをどう変えても変わってはいけないので、テストで固定する対象はこちらです。

## 次の章

[第7章 完成形を通読する](../07-full-app/)
