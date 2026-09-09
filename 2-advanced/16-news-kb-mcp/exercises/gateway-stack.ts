// ハンズオン 16.6: AgentCore Gateway の読み取り経路。
// Cognito（第19章と同じ形）とツール Lambda は完成済み。
// Gateway 本体（L1 CfnGateway）と Lambda ターゲット（CfnGatewayTarget）を書く。
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as agentcore from 'aws-cdk-lib/aws-bedrockagentcore';
import { Construct } from 'constructs';
import * as path from 'path';

export interface NewsGatewayStackProps extends cdk.StackProps {
  readonly articleBucket: s3.IBucket;
  readonly knowledgeBaseId: string;
}

export class NewsGatewayStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: NewsGatewayStackProps) {
    super(scope, id, props);

    // ── Cognito（完成済み。第19章 19.2.2 と同じ判断）─────────────
    const pool = new cognito.UserPool(this, 'UserPool', {
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    const client = pool.addClient('McpClient', {
      authFlows: { userPassword: true }, // 16.8 で CLI からトークンを取るため
      generateSecret: false,
    });
    const discoveryUrl = `${pool.userPoolProviderUrl}/.well-known/openid-configuration`;

    // ── ツール Lambda（完成済み）。ロジックは lambda_src/tools/tools_handler.py ──
    const toolsFn = new lambda.Function(this, 'ToolsFn', {
      runtime: lambda.Runtime.PYTHON_3_13,
      architecture: lambda.Architecture.ARM_64,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda_src/tools')),
      timeout: cdk.Duration.seconds(30),
      environment: {
        KNOWLEDGE_BASE_ID: props.knowledgeBaseId,
        ARTICLE_BUCKET: props.articleBucket.bucketName,
      },
    });
    props.articleBucket.grantRead(toolsFn);
    toolsFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:Retrieve'],
      resources: [`arn:aws:bedrock:${this.region}:${this.account}:knowledge-base/${props.knowledgeBaseId}`],
    }));

    // ── Gateway の実行ロール（完成済み。第18章 18.2.2 と同じ confused deputy 対策）──
    const gatewayRole = new iam.Role(this, 'GatewayRole', {
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com', {
        conditions: { StringEquals: { 'aws:SourceAccount': this.account } },
      }),
    });
    toolsFn.grantInvoke(gatewayRole);

    // TODO(1): agentcore.CfnGateway を作る。
    //   - name: 'aws-news-handson' / roleArn: gatewayRole.roleArn
    //   - protocolType: 'MCP' / authorizerType: 'CUSTOM_JWT'
    //   - authorizerConfiguration: { customJwtAuthorizer: { discoveryUrl,
    //       allowedClients: [client.userPoolClientId] } }（第19章 19.2.1 と同じ構造）

    // TODO(2): agentcore.CfnGatewayTarget で 2 ツールを公開する。
    //   - gatewayIdentifier: gateway.attrGatewayIdentifier / name: 'news-tools'
    //   - credentialProviderConfigurations: [{ credentialProviderType: 'GATEWAY_IAM_ROLE' }]
    //   - targetConfiguration: { mcp: { lambda: { lambdaArn: toolsFn.functionArn,
    //       toolSchema: { inlinePayload: [ search_aws_updates と get_article の ToolDefinition ] } } } }
    //   ツール定義の description は第3章の 3 節構成（受け取るもの / 返すもの / 含まないもの）で書く。
    //   inputSchema は { type: 'object', properties: {...}, required: [...] } の形
    //   （query は string 必須。since_days は integer、category / source は string で任意。
    //     get_article は s3_key: string 必須）。

    // TODO(3): CfnOutput を 3 つ出す。16.8 の接続で使う。
    //   - GatewayUrl: gateway.attrGatewayUrl
    //   - UserPoolId: pool.userPoolId / ClientId: client.userPoolClientId
  }
}
