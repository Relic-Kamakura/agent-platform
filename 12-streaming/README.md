# 第11章 フロントエンドとストリーミング

この章を終えると、JWT 検証つきの Route Handler を自分で書き、エージェントの
進捗をストリーミングで表示する画面が手元で動くようになります。

Next.js（App Router）の骨組みは用意してあります。書くのはサーバ側の 1 ファイル、
`app/api/invoke/route.ts` です。

```bash
cd 11-frontend
npm ci
cp .env.local.example .env.local
```

## 11.1 経路設計 — なぜ Route Handler を挟むのか

ブラウザから AgentCore Runtime を直接呼ぶ構成にすると、AWS の認証情報か
署名の仕組みをブラウザに置くことになります。そこで間にサーバ側の
Route Handler を挟みます。

```
ブラウザ ── アクセストークン ──→ /api/invoke（Route Handler）
                                   ① JWT を検証（aws-jwt-verify）
                                   ② AWS SDK で InvokeAgentRuntime（認証情報はサーバのみ）
                                   ③ 応答ストリームをそのまま返す
```

`lib/backend.ts`（提供コード）が②を担当します。`LOCAL_AGENT_URL` があれば
ローカルの 07-full-app へ、無ければ Runtime へ転送する 2 経路です。
おかげで、この章のハンズオンはデプロイなしで一気通貫できます。

## 11.2 JWT 検証の実装

検証は `aws-jwt-verify` に任せます。自前で JWKS を取りに行く必要はありません。

- `CognitoJwtVerifier.create({userPoolId, clientId, tokenUse: "access"})` を
  **モジュールスコープで 1 度だけ**作る。JWKS がプロセス内にキャッシュされ、
  リクエストごとの鍵取得を避けられる
- `verify(token)` が署名・発行者・client_id・有効期限をまとめて検証する
- API の認可に使うのはアクセストークン（第10章 10.2）

`AUTH_BYPASS` は開発専用の抜け道です。安全に作るコツは 2 つ。判定は
文字列 `"true"` との厳密比較にする（`1` や `yes` で有効にならない）。
そしてバイパス時も**認可以外の検証（prompt の必須チェック等）は省かない**。

## 11.3 ストリーミング

エージェントの調査は数十秒かかります。無反応の画面は「壊れた」と誤解されるので、
進捗を流します。本体 07-full-app は payload に `"stream": true` を付けると
SSE（text/event-stream）で応答します（第7章の `src/streaming.py`）。

流れてくるイベントは 3 種類です。

- `{"event": "stage", "stage": "research" | "review" | "revise"}` — 進捗
- `{"event": "result", ...}` — 最終レポート
- `{"event": "error", "detail": ...}` — 失敗

Route Handler の仕事は、このストリームを**変換せずそのまま**ブラウザへ返すことです。
`await upstream.text()` のように全部読み切ってから返すと、ストリーミングの意味が
消えます。`new Response(upstream.body, ...)` と body を渡すだけでよい。

タイムアウト設計も知っておいてください。AgentCore は同期 15 分・ストリーミング
60 分（第8章）。ストリーミングは UX のためだけでなく、長い処理を接続断で
失わないための選択でもあります。

## 11.4 【ハンズオン】route.ts を書く

`app/api/invoke/route.ts` を新規作成してください。要件:

1. `POST` ハンドラをエクスポートする
2. `AUTH_BYPASS === "true"` なら認可をスキップ。それ以外は
   `Authorization: Bearer <token>` を `CognitoJwtVerifier` で検証し、
   無い・無効なら **401** を返す
3. body の `prompt` が空なら **400**
4. `lib/backend.ts` の `invokeBackend()` に転送し、応答を
   **ストリームのまま**返す（Content-Type も引き継ぐ）

書けたら判定します。

```bash
./verify/verify.sh
```

詰まったら `solutions/route.ts` を見てください。

## 11.5 【ハンズオン・要 Bedrock】ローカル一気通貫

デプロイ不要で、ブラウザ → Route Handler → ローカルエージェント → Bedrock の
全経路を動かします（Bedrock を呼ぶため AWS 認証は必要）。

ターミナル 1 でエージェントを起動します。

```bash
cd 07-full-app && uv run python -m src.main
```

ターミナル 2 でフロントエンドを起動します（`.env.local` は
`AUTH_BYPASS=true` と `LOCAL_AGENT_URL=http://127.0.0.1:8080` のまま）。

```bash
cd 11-frontend && npm run dev
```

http://localhost:3000 を開き「調査する」を押すと、「調査中…」「検証中…」の
進捗が順に現れ、最後にレポートが表示されるはずです。
mock プロバイダのままなので検索は固定データです。

## 11.6 【要 AWS】本番経路

第10章のデプロイ後、`.env.local` を本番向けに切り替えます。
`AUTH_BYPASS=false`、`LOCAL_AGENT_URL` を消し、`AGENT_RUNTIME_ARN` と
`COGNITO_*` を CfnOutput の値で埋める。第10章 10.5 で取得したアクセストークンを
`Authorization` ヘッダに付けて呼び出し、トークン無しが 401 になることも確認します。
Amplify Hosting へのデプロイは、この構成がそのまま載ります。

## 次の章

[第12章 評価と改善ループ](../12-evaluation/)
