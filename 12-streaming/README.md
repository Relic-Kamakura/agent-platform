# 第12章 フロントエンドとストリーミング

この章を終えると、JWT 検証つきの Route Handler を自分で書き、エージェントの進捗をストリーミングで表示する画面が手元で動くようになります。
Next.js（App Router）の骨組みは用意してあり、書くのはサーバ側の 1 ファイルだけです。

最初に依存を入れ、開発用の設定ファイルを作ってください。

```bash
cd 12-streaming
npm ci
cp .env.local.example .env.local
```

## 12.1 概要

### 12.1.1 ストリーミング

ストリーミングは、応答の完成を待たずに、できた部分から順に送り続ける方式です。
エージェントの調査は数十秒かかります。無反応の画面が数十秒続くと、利用者は処理が止まったと判断するため、進捗を順に表示します。

画面のためだけではありません。
AgentCore Runtime のタイムアウトは同期よりストリーミングの方が長く取られています（第8章、値は versions.md）。
同期呼び出しでは上限を超えた処理が打ち切られるため、ストリーミングは長い処理の結果を失わないための選択でもあります。

### 12.1.2 リクエストが通る経路

ブラウザから AgentCore Runtime を直接呼ぶ構成にすると、AWS の認証情報か署名の仕組みをブラウザに置くことになります。
そこで間にサーバ側の Route Handler を挟みます。

```
ブラウザ ── アクセストークン ──→ /api/invoke（Route Handler）
                                   ① JWT を検証（aws-jwt-verify）
                                   ② AWS SDK で InvokeAgentRuntime（認証情報はサーバのみ）
                                   ③ 応答ストリームをそのまま返す
```

②は提供コード `lib/backend.ts` が担当します。
`LOCAL_AGENT_URL` があればローカルの 07-full-app へ、無ければ Runtime へ転送するので、デプロイなしで動かせます。
この章で書くのは①と③、JWT の検証とストリームの受け渡しです。

## 12.2 実装のポイント

### 12.2.1 JWT 検証

検証は `aws-jwt-verify` に任せます。自前で JWKS を取りに行く必要はありません。

`CognitoJwtVerifier.create({userPoolId, clientId, tokenUse: "access"})` は
モジュールスコープで 1 度だけ作ります。JWKS がプロセス内にキャッシュされ、
リクエストごとの鍵取得を避けられるからです。
あとは `verify(token)` が署名、発行者、client_id、有効期限をまとめて検証します。
API の認可に使うのはアクセストークンです（第11章 11.1.3）。

`AUTH_BYPASS` は、開発時に限って JWT 検証を省略するための設定です。
判定は文字列 `"true"` との厳密比較にします。truthy な値をすべて通す判定だと、`1` や `yes` のような意図しない値でも検証が消えるためです。
バイパスするのは認可だけで、prompt の必須チェックなど他の検証は省きません。

### 12.2.2 ストリームの受け渡し

本体 07-full-app は payload に `"stream": true` を付けると SSE（text/event-stream）で応答します（第7章の `src/streaming.py`）。
届くイベントは 3 種類です。

- 進捗は `{"event": "stage", "stage": "research" | "review" | "revise"}`
- 最終レポートは `{"event": "result", ...}`
- 失敗は `{"event": "error", "detail": ...}`

Route Handler の仕事は、このストリームを変換せずそのままブラウザへ返すことです。
`await upstream.text()` のように全部読み切ってから返すと、完了までブラウザに何も届かず、ストリーミングになりません。
`new Response(upstream.body, ...)` のように body を渡すだけにします。

## 12.3 ハンズオン: JWT 検証つきの Route Handler を実装する

JWT を検証してバックエンドへ転送する Route Handler を作ります。
編集するのは `app/api/invoke/route.ts` の 1 ファイルだけです。

### 12.3.1 骨組みをコピーする

```bash
mkdir -p app/api/invoke
cp exercises/route.ts app/api/invoke/route.ts
```

Next.js の App Router はファイルの場所が URL になるため、この配置だけで `POST /api/invoke` が有効になります。

### 12.3.2 TODO を 3 つ埋める

`app/api/invoke/route.ts` を開いてください。
Verifier の生成と prompt の必須チェックは書いてあり、TODO が 3 つ残っています。

1. `AUTH_BYPASS` の分岐。文字列 `'true'` のときだけ認可をスキップする（12.2.1 の厳密比較）
2. JWT 検証。`Authorization: Bearer <token>` を取り出して `verifier.verify()` にかけ、無いか無効なら 401 を返す
3. 転送。`invokeBackend()` の応答をストリームのまま返す。status と Content-Type も引き継ぐ（12.2.2）

### 12.3.3 合格判定

実装できたら TODO コメントを消し、判定します。
実装の構造検査と `tsc --noEmit` の型チェックを行います。

```bash
./verify/verify.sh
```

「第12章 合格。」が出るはずです。

<details>
<summary>解答例</summary>

```typescript
async function authorize(request: NextRequest): Promise<Response | null> {
  // 開発時のバイパス。文字列 "true" のときだけ有効にする
  if (process.env.AUTH_BYPASS === 'true') {
    return null;
  }
  if (!verifier) {
    return Response.json(
      { error: 'COGNITO_USER_POOL_ID / COGNITO_CLIENT_ID が未設定です。' },
      { status: 500 },
    );
  }

  const header = request.headers.get('authorization') ?? '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : '';
  if (!token) {
    return Response.json({ error: 'Authorization: Bearer <token> が必要です。' }, { status: 401 });
  }

  try {
    await verifier.verify(token); // 署名・iss・client_id・有効期限を検証
    return null;
  } catch {
    return Response.json({ error: 'トークンが無効です。' }, { status: 401 });
  }
}

export async function POST(request: NextRequest): Promise<Response> {
  const denied = await authorize(request);
  if (denied) {
    return denied;
  }

  const body = (await request.json()) as InvokePayload;
  if (!body.prompt?.trim()) {
    return Response.json({ error: 'prompt が必要です。' }, { status: 400 });
  }

  // バックエンドの応答（SSE または JSON）をそのままブラウザへ返す
  const upstream = await invokeBackend(body);
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      'Content-Type': upstream.headers.get('Content-Type') ?? 'application/json',
    },
  });
}
```

全文は `solutions/route.ts` にあります。

</details>

## 12.4 ハンズオン: ローカルで全経路を動かす

デプロイ不要で、ブラウザ → Route Handler → ローカルエージェント → Bedrock の全経路を動かします。

ターミナル 1 でエージェントを起動します。

```bash
cd 07-full-app && uv run python -m src.main
```

ターミナル 2 でフロントエンドを起動します。
`.env.local` は `AUTH_BYPASS=true` と `LOCAL_AGENT_URL=http://127.0.0.1:8080` のままにしてください。

```bash
cd 12-streaming && npm run dev
```

http://localhost:3000 を開き「調査する」を押すと、「調査中…」「検証中…」の進捗が順に現れ、最後にレポートが表示されるはずです。
mock プロバイダのままなので検索は固定データです。

## 12.5 本番経路

第11章のデプロイ後、`.env.local` を本番向けに切り替えます。
`AUTH_BYPASS=false` にし、`LOCAL_AGENT_URL` を消し、`AGENT_RUNTIME_ARN` と `COGNITO_*` を CfnOutput の値で埋めます。
第11章 11.4 で取得したアクセストークンを `Authorization` ヘッダに付けて呼び出し、トークン無しが 401 になることも確認してください。
Amplify Hosting などへのデプロイは、この教材では扱いません。

本番に出すなら、画面に評価の導線も付けておきます。
応答の下に親指の上下を置き、押された結果を `request_id` と一緒に保存する、という程度のものです。
これが利用者の満足度（CSAT）の一次データになります。

後から付け足せないのは、押された時点のプロンプトとモデルと検索結果が残っていないと、低評価の理由を追えないからです。
`request_id` で紐付く先が無ければ、集まるのは不満が 3 割という数字だけで、何を直せばいいかは分かりません。
導線と紐付けは最初から入れます。

## 12.6 まとめ

Route Handler がするのは JWT の検証と応答の転送だけです。
AWS の認証情報はサーバ側にだけ置き、入口で JWT を検証し、通ったリクエストの応答ストリームは変換せずそのまま返します。
読み切ってから返すと進捗がブラウザに届かなくなるので、間に処理を挟まないことがストリーミングの条件です。
次の第13章では、この画面に流れてくる報告の品質そのものを evals で測ります。

## 次の章

[第13章 評価と改善ループ](../13-evaluation/)
