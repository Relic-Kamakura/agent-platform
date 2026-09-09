// 第16章の模範解答: AgentCore Gateway の読み取り経路（exercises/gateway-stack.ts の完成形）。
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

    const pool = new cognito.UserPool(this, 'UserPool', {
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    const client = pool.addClient('McpClient', {
      authFlows: { userPassword: true }, // 16.6 で CLI からトークンを取るため
      generateSecret: false,
    });
    const discoveryUrl = `${pool.userPoolProviderUrl}/.well-known/openid-configuration`;

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

    const gatewayRole = new iam.Role(this, 'GatewayRole', {
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com', {
        conditions: { StringEquals: { 'aws:SourceAccount': this.account } },
      }),
    });
    toolsFn.grantInvoke(gatewayRole);

    const gateway = new agentcore.CfnGateway(this, 'NewsGateway', {
      name: 'aws-news-handson',
      roleArn: gatewayRole.roleArn,
      protocolType: 'MCP',
      authorizerType: 'CUSTOM_JWT',
      authorizerConfiguration: {
        customJwtAuthorizer: {
          discoveryUrl,
          allowedClients: [client.userPoolClientId],
        },
      },
    });

    new agentcore.CfnGatewayTarget(this, 'NewsToolsTarget', {
      gatewayIdentifier: gateway.attrGatewayIdentifier,
      name: 'news-tools',
      credentialProviderConfigurations: [{ credentialProviderType: 'GATEWAY_IAM_ROLE' }],
      targetConfiguration: {
        mcp: {
          lambda: {
            lambdaArn: toolsFn.functionArn,
            toolSchema: {
              inlinePayload: [
                {
                  name: 'search_aws_updates',
                  description: [
                    'AWS の更新情報ナレッジベースを意味検索する。',
                    '受け取るもの: query（検索したい内容。必須）、since_days（何日前まで。任意）、',
                    'category / source（whats-new, news-blog, jp-blog のいずれか。任意）。',
                    '返すもの: スコア・タイトル・URL・抜粋・published_at・s3_key のリスト（最大 5 件）。',
                    '含まないもの: 記事の全文（全文は get_article で取る）。要約や意見。',
                  ].join(' '),
                  inputSchema: {
                    type: 'object',
                    properties: {
                      query: { type: 'string', description: '検索クエリ' },
                      since_days: { type: 'integer', description: '何日前までに絞るか' },
                      category: { type: 'string', description: 'カテゴリ名（RSS の category）' },
                      source: { type: 'string', description: 'whats-new / news-blog / jp-blog' },
                    },
                    required: ['query'],
                  },
                },
                {
                  name: 'get_article',
                  description: [
                    '記事 1 件の Markdown 全文を取得する。',
                    '受け取るもの: s3_key（search_aws_updates が返した s3_key をそのまま渡す）。',
                    '返すもの: s3_key と markdown 全文。',
                    '含まないもの: 検索。要約。',
                  ].join(' '),
                  inputSchema: {
                    type: 'object',
                    properties: {
                      s3_key: { type: 'string', description: '記事の S3 キー' },
                    },
                    required: ['s3_key'],
                  },
                },
              ],
            },
          },
        },
      },
    });

    new cdk.CfnOutput(this, 'GatewayUrl', { value: gateway.attrGatewayUrl });
    new cdk.CfnOutput(this, 'UserPoolId', { value: pool.userPoolId });
    new cdk.CfnOutput(this, 'ClientId', { value: client.userPoolClientId });
  }
}
