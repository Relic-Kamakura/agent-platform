// エージェント基盤への転送ヘルパー（提供コード。ハンズオン対象は route.ts 側）。
//
// LOCAL_AGENT_URL が設定されていればローカルのエージェント（:8080）へ、
// 無ければ AgentCore Runtime（AGENT_RUNTIME_ARN）へ転送する。
// どちらもレスポンスはストリームのまま返し、Route Handler がブラウザへ返す。
import {
  BedrockAgentCoreClient,
  InvokeAgentRuntimeCommand,
} from '@aws-sdk/client-bedrock-agentcore';
import { NodeHttpHandler } from '@smithy/node-http-handler';

// リクエスト全体の上限。既定の requestTimeout は 0（無制限）なので明示する。
// ストリーミングは同期呼び出しより長く待てるため、ストリーミング前提なら伸ばす
const REQUEST_TIMEOUT_MS = 15 * 60 * 1000;

export interface InvokePayload {
  prompt: string;
  stream?: boolean;
  request_id?: string;
}

/** ローカルで起動したエージェントへ転送する（開発時）。 */
async function invokeLocal(baseUrl: string, payload: InvokePayload): Promise<Response> {
  return fetch(`${baseUrl}/invocations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

/** AgentCore Runtime へ転送する（デプロイ済み環境）。 */
async function invokeRuntime(payload: InvokePayload): Promise<Response> {
  const arn = process.env.AGENT_RUNTIME_ARN;
  if (!arn) {
    return Response.json(
      { error: 'AGENT_RUNTIME_ARN か LOCAL_AGENT_URL を設定してください。' },
      { status: 500 },
    );
  }

  const client = new BedrockAgentCoreClient({
    region: process.env.AWS_REGION,
    // JS SDK の既定は maxAttempts 3。5xx や 409 を再試行されると同じ runtimeSessionId で
    // エージェントが二重に走り、Bedrock のトークン費用も二重に出る。再試行は呼び出し側で決める
    maxAttempts: 1,
    requestHandler: new NodeHttpHandler({
      connectionTimeout: 5_000,
      requestTimeout: REQUEST_TIMEOUT_MS,
    }),
  });
  const command = new InvokeAgentRuntimeCommand({
    agentRuntimeArn: arn,
    // セッション ID は 33 文字以上必要。UUID と時刻で満たす。
    // ワンショット設計なので毎リクエスト新しく作る。会話を続けるなら会話単位で使い回す
    runtimeSessionId: `${crypto.randomUUID().replaceAll('-', '')}${Date.now()}`,
    payload: new TextEncoder().encode(JSON.stringify(payload)),
  });
  const result = await client.send(command);

  // response はストリーム。そのまま Web Response に包んでブラウザへ返す
  const body = result.response
    ? (result.response.transformToWebStream() as ReadableStream)
    : null;
  return new Response(body, {
    headers: { 'Content-Type': result.contentType ?? 'application/json' },
  });
}

export async function invokeBackend(payload: InvokePayload): Promise<Response> {
  const localUrl = process.env.LOCAL_AGENT_URL;
  return localUrl ? invokeLocal(localUrl, payload) : invokeRuntime(payload);
}
