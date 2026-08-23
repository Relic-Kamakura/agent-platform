# 演習 04 模範解答

2 ファイルに手を入れる。

## 1. `07-full-app/src/guards.py` — CostLimiter の追加

[guards_additions.py](guards_additions.py) のクラスを追加し、`Guards` と `build_guards` を次のように変更する:

```python
@dataclass
class Guards:
    tool_limiter: ToolCallLimiter
    turn_limiter: TurnLimiter
    cost_limiter: CostLimiter          # 追加
    usage_logger: UsageLogger

    @property
    def hooks(self) -> list[HookProvider | HookCallback[Any]]:
        return [self.tool_limiter, self.turn_limiter, self.cost_limiter, self.usage_logger]


def build_guards(settings: Settings, role: str) -> Guards:
    return Guards(
        tool_limiter=ToolCallLimiter(
            max_total=settings.max_tool_calls_total,
            max_per_tool=settings.max_tool_calls_per_tool,
        ),
        turn_limiter=TurnLimiter(max_turns=settings.max_agent_turns),
        cost_limiter=CostLimiter(max_total_tokens=settings.max_total_input_tokens),  # 追加
        usage_logger=UsageLogger(role=role),
    )
```

## 2. `07-full-app/src/config.py` — 設定の追加

「コスト・暴走対策」の節に追加する:

```python
    # 1 リクエストで消費してよい入力トークンの概算上限。
    # 根拠: 既定モデルの単価と「1 リクエスト数十円まで」という運用目安から逆算した暫定値。
    # 実測（token_usage ログ）を集計してから調整すること。
    max_total_input_tokens: int = Field(default=50_000, ge=1000)
```
