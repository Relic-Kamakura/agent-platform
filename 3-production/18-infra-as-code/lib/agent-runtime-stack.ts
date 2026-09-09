import { CfnOutput, Stack, type StackProps } from 'aws-cdk-lib';
import * as agentcore from 'aws-cdk-lib/aws-bedrockagentcore';
import * as iam from 'aws-cdk-lib/aws-iam';
import type { Construct } from 'constructs';
import type { PlatformConfig } from './config';

export interface AgentRuntimeStackProps extends StackProps {
  /**
   * Cognito User Pool の OIDC discovery URL。
   * 指定すると Runtime に inbound JWT authorizer を設定する。
   * Phase 3 の AuthStack から渡す。未指定なら IAM (SigV4) 認証のみになる。
   */
  readonly jwtDiscoveryUrl?: string;
  readonly jwtAllowedClients?: string[];
}

/**
 * AgentCore Runtime。
 *
 * aws-cdk-lib には L2 の Runtime もあるが、ここでは L1 (CfnRuntime) で書く。
 * プロパティが CloudFormation リファレンスと 1 対 1 で読めるほうが教材として追いやすいため。
 *
 * VPC は作らない。networkMode: 'PUBLIC' で AgentCore のマネージドネットワークを使う。
 */
export class AgentRuntimeStack extends Stack {
  public readonly runtime: agentcore.CfnRuntime;

  constructor(
    scope: Construct,
    id: string,
    config: PlatformConfig,
    props: AgentRuntimeStackProps = {},
  ) {
    super(scope, id, props);

    const executionRole = this.resolveExecutionRole(config);

    // ECR のイメージ URI。ハードコードせずアカウント / リージョン / context から組み立てる。
    const containerUri =
      `${this.account}.dkr.ecr.${this.region}.amazonaws.com/` +
      `${config.ecrRepositoryName}:${config.imageTag}`;

    this.runtime = new agentcore.CfnRuntime(this, 'AgentRuntime', {
      agentRuntimeName: config.runtimeName,
      // CloudFormation の Description は ASCII のみ許容される。日本語を入れると検証警告になる。
      description: 'Competitive research agent (Strands Agents)',
      roleArn: executionRole,
      agentRuntimeArtifact: {
        containerConfiguration: { containerUri },
      },
      // VPC を使わない構成。AgentCore のマネージドネットワークで外部へ出る。
      networkConfiguration: { networkMode: 'PUBLIC' },
      protocolConfiguration: 'HTTP',
      environmentVariables: config.agentEnvironment,
      ...(props.jwtDiscoveryUrl
        ? {
            authorizerConfiguration: {
              customJwtAuthorizer: {
                discoveryUrl: props.jwtDiscoveryUrl,
                ...(props.jwtAllowedClients?.length
                  ? { allowedClients: props.jwtAllowedClients }
                  : {}),
              },
            },
          }
        : {}),
    });

    new CfnOutput(this, 'AgentRuntimeArn', {
      value: this.runtime.attrAgentRuntimeArn,
      description: 'ARN passed to InvokeAgentRuntime',
      exportName: `${this.stackName}-AgentRuntimeArn`,
    });
  }

  /**
   * 実行ロールを解決する。
   * context に agentcoreExecutionRoleArn があれば既存ロールを使い、無ければ新規作成する。
   * ロールを自分で作れない環境と、作れる環境の両方に対応するため。
   */
  private resolveExecutionRole(config: PlatformConfig): string {
    if (config.executionRoleArn) {
      return config.executionRoleArn;
    }

    const role = new iam.Role(this, 'AgentRuntimeExecutionRole', {
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com', {
        conditions: {
          StringEquals: { 'aws:SourceAccount': this.account },
          ArnLike: {
            'aws:SourceArn': `arn:aws:bedrock-agentcore:${this.region}:${this.account}:*`,
          },
        },
      }),
      description: 'Execution role assumed by AgentCore Runtime',
    });

    // ECR からイメージを取得する
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          'ecr:BatchGetImage',
          'ecr:GetDownloadUrlForLayer',
          'ecr:BatchCheckLayerAvailability',
        ],
        resources: [
          `arn:aws:ecr:${this.region}:${this.account}:repository/${config.ecrRepositoryName}`,
        ],
      }),
    );
    role.addToPolicy(
      new iam.PolicyStatement({ actions: ['ecr:GetAuthorizationToken'], resources: ['*'] }),
    );

    // Bedrock のモデルを呼ぶ。
    // 推論プロファイルを指定した呼び出しでは、IAM がプロファイルとルーティング先リージョンの
    // 基盤モデルの両方を評価する。片方だけの許可では AccessDeniedException になる。
    // モデル ID を実行時に差し替えられるようワイルドカードにしている。本番では
    // aws bedrock get-inference-profile の models[].modelArn に出る ARN へ絞ること。
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: [
          `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/*`,
          `arn:aws:bedrock:*::foundation-model/*`,
        ],
      }),
    );

    // CloudWatch Logs。ロググループの作成と一覧参照、ログイベントの書き込み。
    // 対象は Runtime のロググループに限定する。
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['logs:CreateLogGroup', 'logs:DescribeLogStreams'],
        resources: [
          `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/bedrock-agentcore/runtimes/*`,
        ],
      }),
    );
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['logs:CreateLogStream', 'logs:PutLogEvents'],
        resources: [
          `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*`,
        ],
      }),
    );
    // DescribeLogGroups はロググループ単位に絞れない（一覧を引く API のため）。
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['logs:DescribeLogGroups'],
        resources: [`arn:aws:logs:${this.region}:${this.account}:log-group:*`],
      }),
    );

    // X-Ray へのトレース送信を許可するステートメントは 18.3 で自分で追加する。

    // CloudWatch メトリクス。namespace の条件で bedrock-agentcore 以外への書き込みを塞ぐ。
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['cloudwatch:PutMetricData'],
        resources: ['*'],
        conditions: { StringEquals: { 'cloudwatch:namespace': 'bedrock-agentcore' } },
      }),
    );

    // ワークロードアクセストークンの取得。AgentCore Identity 経由で外部 API を呼ぶときに使う。
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          'bedrock-agentcore:GetWorkloadAccessToken',
          'bedrock-agentcore:GetWorkloadAccessTokenForJWT',
          'bedrock-agentcore:GetWorkloadAccessTokenForUserId',
        ],
        resources: [
          `arn:aws:bedrock-agentcore:${this.region}:${this.account}:workload-identity-directory/default`,
          `arn:aws:bedrock-agentcore:${this.region}:${this.account}:workload-identity-directory/default/workload-identity/${config.runtimeName}-*`,
        ],
      }),
    );

    return role.roleArn;
  }
}
