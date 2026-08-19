// エージェント基盤への転送ヘルパー（提供コード。第11章のハンズオン対象は route.ts 側）。
//
// LOCAL_AGENT_URL が設定されていればローカルの 07-full-app（:8080）へ、
// 無ければ AgentCore Runtime（AGENT_RUNTIME_ARN）へ転送する。
// どちらもレスポンスはストリームのまま返し、Route Handler がブラウザへ流す。
import {
  BedrockAgentCoreClient,
  InvokeAgentRuntimeCommand,
} from '@aws-sdk/client-bedrock-agentcore';

export interface InvokePayload {
  prompt: string;
  stream?: boolean;
  request_id?: string;
}

/** ローカルの 07-full-app へ転送する（開発時）。 */
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

  const client = new BedrockAgentCoreClient({ region: process.env.AWS_REGION });
  const command = new InvokeAgentRuntimeCommand({
    agentRuntimeArn: arn,
    // セッション ID は 33 文字以上が必要（第8章）。UUID + 時刻で満たす
    runtimeSessionId: `${crypto.randomUUID().replaceAll('-', '')}${Date.now()}`,
    payload: new TextEncoder().encode(JSON.stringify(payload)),
  });
  const result = await client.send(command);

  // response はストリーム。そのまま Web Response に包んでブラウザへ流す
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
