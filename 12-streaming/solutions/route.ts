// 第12章の模範解答。app/api/invoke/route.ts として配置する。
//
// このファイルがアプリ側の JWT 検証の入口。ブラウザからの呼び出しはすべてここを通り、
// JWT を検証してからエージェント基盤へ転送する。AWS 認証情報はサーバ側にしか無い。
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

  // バックエンドの応答（SSE または JSON）をそのままブラウザへ流す
  const upstream = await invokeBackend(body);
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      'Content-Type': upstream.headers.get('Content-Type') ?? 'application/json',
    },
  });
}
