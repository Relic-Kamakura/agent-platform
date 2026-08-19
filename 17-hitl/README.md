# 第17章 HITL — 人間の承認を挟む

この章を終えると、「危険なツールは人間の承認が下りるまで実行しない」という
承認ゲートを hooks で実装できるようになります。完全オフラインで完結する章です。

## 17.1 なぜ承認ゲートか

いまのエージェントのツールは読み取り専用（検索・取得）です。しかし案件では
すぐに「メールを送る」「チケットを起票する」「DB を更新する」ツールが要求されます。
読み取りと書き込みでは失敗の重さが違います。誤検索はやり直せますが、
誤送信は取り消せません。

HITL（Human-in-the-Loop）は、この非対称に対する設計です。すべてを人間が
確認するのでは自動化の意味がなく、すべてを自動にすると事故が取り返せない。
そこで**取り消せない操作だけ**に人間の承認を挟みます。

判断基準は第5章の「裁量とコードの境界」と同じ形をしています。
その操作が誤って実行されたとき、誰かが困るか。困るなら承認ゲート。

## 17.2 実装の考え方

第4章で学んだとおり、`BeforeToolCallEvent` はツール実行の直前に割り込め、
`event.cancel_tool` に文字列を入れると実行をキャンセルして理由をモデルに返せます。
承認ゲートはこの仕組みの応用です。

- 承認が必要なツール名の集合（`requires_approval`）を持つ
- 該当ツールの実行前に、承認関数（`approver`）へツール名と引数を渡して尋ねる
- 承認されたら通し、否認されたら「否認された」という理由付きでキャンセルする

approver を関数として注入するのがポイントです。CLI なら `input()` で人間に聞く、
テストなら常に True/False を返す、本番なら Slack 承認フローに置き換える——
ゲートの実装を変えずに承認手段だけ差し替えられます。

## 17.3 【ハンズオン】ApprovalGate を実装する

`07-full-app/src/guards.py` に `ApprovalGate` を追加してください。

要件:

1. `ApprovalGate(requires_approval: set[str], approver: Callable[[str, dict], bool])` —
   dataclass の `HookProvider`
2. `BeforeToolCallEvent` で、ツール名が `requires_approval` に**含まれない**場合は
   何もしない（読み取り系ツールを遅くしない）
3. 含まれる場合は `approver(ツール名, ツール入力)` を呼ぶ。
   ツール入力は `event.tool_use.get("input", {})` から取る
4. 否認されたら `event.cancel_tool` に理由の文字列を入れる。理由には
   ツール名と「人間の承認が得られなかった」ことを含め、モデルが代替行動
   （実行せずに下書きを提示する等）に移れる文にする
5. 承認・否認のどちらでも `log_event` で記録を残す（`message="approval_requested"`、
   `approved=True/False`。監査の土台になる）

判定を流します（AWS 不要・完全オフライン）。

```bash
uv run --project 07-full-app pytest 17-hitl/verify -q
```

`4 passed` で合格です。

## 17.4 使いどころのイメージ

このゲートを実際に使うときの形も見ておいてください（実装は不要）。

```python
def cli_approver(tool_name: str, tool_input: dict) -> bool:
    print(f"エージェントが {tool_name} を実行しようとしています: {tool_input}")
    return input("承認しますか？ [y/N]: ").strip().lower() == "y"

guards = build_guards(settings, role="orchestrator")
gate = ApprovalGate(requires_approval={"send_email", "create_ticket"}, approver=cli_approver)
agent = Agent(..., hooks=[*guards.hooks, gate])
```

同期の `input()` はローカル専用です。AgentCore Runtime 上では応答を返せないので、
本番では「承認待ちをキューに積んで一時停止し、承認 API で再開する」形になります。
その非同期版は AgentCore の組み込み機能や Step Functions と組み合わせる発展課題です。

## 次の章

[第18章 構造化出力](../18-structured-output/)
