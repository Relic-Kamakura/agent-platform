# 演習 09 模範解答

## 1. `lib/config.ts` — agentEnvironment への追加（1 箇所）

`searchProvider` の処理の直後に、同じパターンで追加する:

```typescript
    ...(app.node.tryGetContext('logLevel')
      ? { LOG_LEVEL: String(app.node.tryGetContext('logLevel')) }
      : {}),
```

## 2. `cdk.json` — context への既定値追加

```json
    "logLevel": "INFO",
```

## ポイント

- `loadConfig()` 以外の場所で `tryGetContext` を呼ばないこと。設定の読み取り口を
  1 箇所に保つのは Python 側（config.py）と同じ規約
- 「未指定なら入れない」の三項スプレッドパターンにより、context を消せば
  Runtime の環境変数からも消える（`.env` 側の既定値が生きる）
