# 第18章 HITL（承認ゲート）

この章を終えると、取り消せない操作を人間の承認が下りるまで実行しない承認ゲートを、hooks で自作できるようになります。
合格判定まではモデルを呼ばず、オフラインで進みます。

この章も独立した uv プロジェクトです。最初に依存を入れてください。

```bash
cd 18-hitl
uv sync
```

## 18.1 概要

### 18.1.1 HITL とは

HITL（Human-in-the-Loop）は、エージェントの判断に人間の承認を挟む設計です。
すべてを人間が確認するなら自動化の意味がなく、すべてを自動にすると誤った操作を取り消せません。
そのため、承認を挟む箇所を絞り込みます。

### 18.1.2 承認が要る操作の判断基準

ここまでの章で作ったツールは読み取り専用（検索・取得）でした。
メール送信、チケット起票、DB 更新のような書き込み系のツールを足すと、失敗の重さが変わります。誤検索はやり直せますが、誤送信は取り消せません。

この非対称に合わせて、取り消せない操作だけに人間の承認を挟みます。
どのツールに承認が要るかはモデルの裁量に任せず、コードで決めます。第5章の「裁量とコードの境界」と同じ判断です。
基準は、その操作が誤って実行されたとき誰かが困るか。困るなら承認ゲートの対象にします。

```mermaid
graph LR
    A["エージェントが<br/>ツールを呼ぼうとする"] --> J{"取り消せない<br/>操作か"}
    J -->|いいえ| T["そのまま実行"]
    J -->|はい| H["人間に尋ねる"]
    H -->|承認| T2["実行"]
    H -->|否認| C["キャンセルし<br/>理由をモデルへ返す"]
```

## 18.2 実装のポイント

### 18.2.1 BeforeToolCallEvent の再利用

第4章で見たとおり、`BeforeToolCallEvent` はツール実行の直前に割り込め、`event.cancel_tool` に文字列を入れると実行をキャンセルして理由をモデルに返せます。
承認ゲートはこの応用で、新しい API は出てきません。
違いは止める条件だけです。回数の上限ではなく、人間の返事で決めます。

ゲートがすることは 3 つです。

- 承認が必要なツール名の集合（`requires_approval`）を持つ
- 該当ツールの実行前に、承認関数（`approver`）へツール名と引数を渡して尋ねる
- 承認されたら通し、否認されたら理由付きでキャンセルする

対象外のツールでは approver を呼びません。
読み取り系ツールまで人間の応答待ちにすると承認の回数が増え、1 件ずつ内容を確かめるのが難しくなるからです。

### 18.2.2 approver の注入

approver は固定実装にせず、`Callable[[str, dict], bool]` として外から注入します。
CLI なら `input()` で人間に尋ね、テストなら固定値を返します。
Slack 承認フローのような別の手段にも、ゲート本体を変えずに差し替えられます。

否認の返し方は第4章の `cancel_tool` と同じで、bool ではなく理由の文字列を渡します。
`True` だけを渡すと、モデルに届くのは `tool cancelled by user` という定型のエラーだけで、なぜ実行できないのかも次に何をすべきかも伝わりません。
承認が得られなかったこと、代わりに下書きを提示すべきことまで書けば、モデルは代替行動に移れます。

## 18.3 【ハンズオン】ApprovalGate を実装する

書き込み系ツールの直前で人間に尋ねるゲートを作ります。
編集するのは `exercises/approval_gate.py` の 1 ファイルだけです。

### 18.3.1 TODO を 3 つ埋める

`exercises/approval_gate.py` を開いてください。
dataclass の枠と approver の型は書いてあり、TODO が 3 つ残っています。

1. `register_hooks` で `BeforeToolCallEvent` に `self._check` を登録する
2. `_check` の前半で、`requires_approval` に含まれないツールはそのまま通す（approver を呼ばない）
3. `_check` の後半で approver に尋ねて結果をログに残し、否認なら `event.cancel_tool` に理由の文字列を入れる

先に判定テスト `verify/test_approval_gate.py` を読むと分かりやすくなります。
イベントを手で作って hook を検証する技法は第4章・第6章と同じです。

### 18.3.2 承認と否認の両方を実行する

実装できたら TODO コメントを消し、判定の前に動かします。
モデルを呼ばずにイベントだけを手で渡すスクリプトを用意してあります（編集不要）。

```bash
uv run 01_run_gate.py
```

対象外のツール、承認、否認の 3 ケースを渡すので、こう表示されるはずです。

```
web_search : cancel_tool=False  approver への問い合わせ=0 回
send_email : cancel_tool=False  （承認されたので実行される）
send_email : 否認。ツール結果としてモデルに渡る理由 ->
  ツール 'send_email' の実行に人間の承認が得られませんでした。実行せずに、代わりに実行内容の下書きを提示してください。
```

### 18.3.3 合格判定

```bash
uv run pytest -q
```

`5 passed` で合格です。
対象外のツールで approver を呼ばないこと、承認なら通すこと、否認の理由が文字列でツール名を含むこと、approver にツールの入力が渡ることを検査します。

<details>
<summary>解答例</summary>

```python
    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(BeforeToolCallEvent, self._check)

    def _check(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use.get("name", "<unknown>")
        if name not in self.requires_approval:
            # 読み取り系ツールを遅くしない。承認対象だけ人間に尋ねる
            return

        tool_input = dict(event.tool_use.get("input", {}))
        approved = self.approver(name, tool_input)
        # どの操作が承認・否認されたかを後から追う監査ログの元データになる
        logger.info("approval_requested tool=%s approved=%s", name, approved)
        if not approved:
            event.cancel_tool = (
                f"ツール '{name}' の実行に人間の承認が得られませんでした。"
                "実行せずに、代わりに実行内容の下書きを提示してください。"
            )
```

全文は `solutions/approval_gate.py` にあります。

</details>

### 18.3.4 エージェントで観察する（任意）

自作したゲートを、Bedrock を呼ぶ実際のエージェントに付けて動かします。

```bash
uv run 02_agent_with_gate.py
```

メール送信を頼むと、モデルが `send_email` を呼ぼうとした瞬間に承認を聞かれます。
`y` なら送信結果（演習用の疑似送信）が、`n` なら実行されないまま、モデルが本文の下書きを提示する応答が返るはずです。
スクリプトには第4章と同じツール回数上限のガードも付けてあります。承認ゲートは取り消せない操作を止め、回数上限は呼び出し回数を抑えるもので、役割が違います。

`input()` は同期なのでローカル実行専用です。
AgentCore Runtime 上では実行中のコンテナに人間が応答を返せないため、Runtime で動かすなら承認待ちをキューに積んで一時停止し、承認後に再開する非同期の形が要ります。
その実装は Step Functions などと組み合わせる発展課題です。

## 18.4 まとめ

承認ゲートは新しい仕組みではなく、第4章の `BeforeToolCallEvent` の止める条件を人間の返事に変えただけのものです。
取り消せない操作かどうかで対象を決め、承認手段は関数として注入します。
この形なら、CLI の `input()` から Slack 承認フローまで、ゲート本体を変えずに差し替えられます。
次の第19章では、テキストのパースという別の故障モードを構造化出力で消します。

## 次の章

[第19章 構造化出力](../19-structured-output/)
