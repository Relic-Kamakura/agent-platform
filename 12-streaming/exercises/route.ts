// ハンズオン 12.3: 認可の門番となる Route Handler の骨組み。
// app/api/invoke/route.ts にコピーして TODO を埋める。
// 実装が終わったら TODO コメントは消す。完成形は solutions/route.ts。
import { CognitoJwtVerifier } from 'aws-jwt-verify';
import type { NextRequest } from 'next/server';

import { invokeBackend, type InvokePayload } from '@/lib/backend';

// Verifier はモジュールスコープで 1 度だけ作る。JWKS（公開鍵）が
// プロセス内にキャッシュされ、リクエストごとの鍵取得を避けられる
const verifier =
  process.env.COGNITO_USER_POOL_ID && process.env.COGNITO_CLIENT_ID
    ? CognitoJwtVerifier.create({
        userPoolId: process.env.COGNITO_USER_POOL_ID,
        clientId: process.env.COGNITO_CLIENT_ID,
        tokenUse: 'access', // API の認可に使うのはアクセストークン（第11章 11.1.3）
      })
    : null;

async function authorize(request: NextRequest): Promise<Response | null> {
  // TODO(1): 開発用バイパス。process.env.AUTH_BYPASS が文字列 'true' のときだけ
  //   検証せずに null を返す（'true' との厳密比較にする理由は 12.2.1）

  if (!verifier) {
    return Response.json(
      { error: 'COGNITO_USER_POOL_ID / COGNITO_CLIENT_ID が未設定です。' },
      { status: 500 },
    );
  }

  // TODO(2): Authorization ヘッダから 'Bearer ' に続くトークンを取り出す。
  //   - トークンが無ければ 401 の Response を返す
  //   - あれば await verifier.verify(token) で検証し、通れば null を返す
  //   - verify が例外を投げたら 401 の Response を返す
  return Response.json({ error: 'TODO(2) が未実装です。' }, { status: 501 });
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

  // TODO(3): await invokeBackend(body) で転送し、応答をストリームのまま返す。
  //   upstream.body を new Response にそのまま渡し、status と Content-Type を引き継ぐ。
  //   await upstream.text() で読み切ると進捗がブラウザに届かなくなる（12.2.2）
  return Response.json({ error: 'TODO(3) が未実装です。' }, { status: 501 });
}
