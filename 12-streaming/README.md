# 第12章 フロントエンドとストリーミング

この章を終えると、JWT 検証つきの Route Handler を自分で書き、エージェントの
進捗をストリーミングで表示する画面が手元で動くようになります。

Next.js（App Router）の骨組みは用意してあります。書くのはサーバ側の 1 ファイル、
`app/api/invoke/route.ts` です。

```bash
cd 12-streaming
npm ci
cp .env.local.example .env.local
```

## 12.1 概要

### 12.1.1 ストリーミングとは

ストリーミングは、応答の完成を待たずに、できた部分から順に送り続ける方式です。
エージェントの調査は数十秒かかります。無反応の画面は「壊れた」と誤解されるので、
進捗を流します。

UX のためだけではありません。AgentCore のタイムアウトは同期 15 分・ストリーミング
60 分です（第8章）。ストリーミングは、長い処理を接続断で失わないための選択でもあります。

### 12.1.2 経路設計 — なぜ Route Handler を挟むのか

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

## 12.2 実装のポイント

### 12.2.1 JWT 検証

検証は `aws-jwt-verify` に任せます。自前で JWKS を取りに行く必要はありません。

- `CognitoJwtVerifier.create({userPoolId, clientId, tokenUse: "access"})` を
  **モジュールスコープで 1 度だけ**作る。JWKS がプロセス内にキャッシュされ、
  リクエストごとの鍵取得を避けられる
- `verify(token)` が署名・発行者・client_id・有効期限をまとめて検証する
- API の認可に使うのはアクセストークン（第11章 11.1.3）

`AUTH_BYPASS` は開発専用の抜け道です。安全に作るコツは 2 つ。判定は
文字列 `"true"` との厳密比較にする（`1` や `yes` で有効にならない）。
そしてバイパス時も**認可以外の検証（prompt の必須チェック等）は省かない**。

### 12.2.2 ストリームを変換せずに返す

本体 07-full-app は payload に `"stream": true` を付けると
SSE（text/event-stream）で応答します（第7章の `src/streaming.py`）。
流れてくるイベントは 3 種類です。

- `{"event": "stage", "stage": "research" | "review" | "revise"}` — 進捗
- `{"event": "result", ...}` — 最終レポート
- `{"event": "error", "detail": ...}` — 失敗

Route Handler の仕事は、このストリームを**変換せずそのまま**ブラウザへ返すことです。
`await upstream.text()` のように全部読み切ってから返すと、ストリーミングの意味が
消えます。`new Response(upstream.body, ...)` と body を渡すだけでよい。

## 12.3 【ハンズオン】route.ts を書く

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

## 12.4 【ハンズオン・要 Bedrock】ローカル一気通貫

デプロイ不要で、ブラウザ → Route Handler → ローカルエージェント → Bedrock の
全経路を動かします（Bedrock を呼ぶため AWS 認証は必要）。

ターミナル 1 でエージェントを起動します。

```bash
cd 07-full-app && uv run python -m src.main
```

ターミナル 2 でフロントエンドを起動します（`.env.local` は
`AUTH_BYPASS=true` と `LOCAL_AGENT_URL=http://127.0.0.1:8080` のまま）。

```bash
cd 12-streaming && npm run dev
```

http://localhost:3000 を開き「調査する」を押すと、「調査中…」「検証中…」の
進捗が順に現れ、最後にレポートが表示されるはずです。
mock プロバイダのままなので検索は固定データです。

## 12.5 【要 AWS】本番経路

第11章のデプロイ後、`.env.local` を本番向けに切り替えます。
`AUTH_BYPASS=false`、`LOCAL_AGENT_URL` を消し、`AGENT_RUNTIME_ARN` と
`COGNITO_*` を CfnOutput の値で埋める。第11章 11.4 で取得したアクセストークンを
`Authorization` ヘッダに付けて呼び出し、トークン無しが 401 になることも確認します。
Amplify Hosting へのデプロイは、この構成がそのまま載ります。

## 12.6 まとめ

Route Handler の役割は **薄い門番** に徹することです。AWS の認証情報はサーバ側に
だけ置き、入口で JWT を検証し、通ったリクエストの応答ストリームは変換せず素通しする。
読み切ってから返した瞬間にストリーミングは死ぬので、「何もしない」ことが実装の核心に
なります。次の第13章では、この画面に流れてくる報告の品質そのものを evals で測ります。
AWS 認証が無い場合は 12.4・12.5 を飛ばし、`docs/aws-checklist.md` で回収してください。

## 次の章

[第13章 評価と改善ループ](../13-evaluation/)
