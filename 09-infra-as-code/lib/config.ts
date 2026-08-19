import type { App } from 'aws-cdk-lib';

/**
 * CDK context を読む唯一の場所。
 * 他のスタックから app.node.tryGetContext() を直接呼ばないこと。
 *
 * 値の与え方:
 *   cdk.json の "context" に既定値を置く
 *   npx cdk deploy -c region=us-east-1 のように上書きする
 */
export interface PlatformConfig {
  /** デプロイ先リージョン。未指定なら CDK_DEFAULT_REGION にフォールバックする。 */
  readonly region: string;
  readonly account?: string;
  readonly ecrRepositoryName: string;
  readonly imageTag: string;
  readonly runtimeName: string;

  /**
   * 既存の AgentCore 実行ロール ARN。
   * 指定があれば CDK はロールを作らずこの ARN を使う。
   * 未指定なら CDK が新規作成する。両方の経路を用意している。
   */
  readonly executionRoleArn?: string;

  /** Runtime に注入する環境変数。モデル ID などをここから渡す。 */
  readonly agentEnvironment: Record<string, string>;

  readonly authBypass: boolean;
}

function requireString(app: App, key: string, fallback?: string): string {
  const value = (app.node.tryGetContext(key) as string | undefined) ?? fallback;
  if (!value) {
    throw new Error(
      `context '${key}' が未設定です。cdk.json に既定値を置くか -c ${key}=... で渡してください。`,
    );
  }
  return value;
}

export function loadConfig(app: App): PlatformConfig {
  // リージョンはハードコードしない。context -> CDK_DEFAULT_REGION の順で解決する。
  const region = requireString(app, 'region', process.env.CDK_DEFAULT_REGION);

  const modelIds = (app.node.tryGetContext('modelIds') ?? {}) as Record<string, string>;

  const agentEnvironment: Record<string, string> = {
    AWS_REGION: region,
    ...(modelIds.orchestrator ? { MODEL_ID_ORCHESTRATOR: modelIds.orchestrator } : {}),
    ...(modelIds.search ? { MODEL_ID_SEARCH: modelIds.search } : {}),
    ...(modelIds.review ? { MODEL_ID_REVIEW: modelIds.review } : {}),
    ...(app.node.tryGetContext('modelIdPrefix') !== undefined
      ? { BEDROCK_MODEL_ID_PREFIX: String(app.node.tryGetContext('modelIdPrefix')) }
      : {}),
    ...(app.node.tryGetContext('searchProvider')
      ? { SEARCH_PROVIDER: String(app.node.tryGetContext('searchProvider')) }
      : {}),
    ...(app.node.tryGetContext('maxToolCallsTotal')
      ? { MAX_TOOL_CALLS_TOTAL: String(app.node.tryGetContext('maxToolCallsTotal')) }
      : {}),
    ...(app.node.tryGetContext('maxAgentTurns')
      ? { MAX_AGENT_TURNS: String(app.node.tryGetContext('maxAgentTurns')) }
      : {}),
  };

  return {
    region,
    account: app.node.tryGetContext('account') ?? process.env.CDK_DEFAULT_ACCOUNT,
    ecrRepositoryName: requireString(app, 'ecrRepositoryName', 'agent-platform/agent'),
    imageTag: requireString(app, 'imageTag', 'latest'),
    runtimeName: requireString(app, 'runtimeName', 'agentPlatformAgent'),
    executionRoleArn: app.node.tryGetContext('agentcoreExecutionRoleArn'),
    agentEnvironment,
    authBypass: String(app.node.tryGetContext('authBypass') ?? 'false') === 'true',
  };
}
