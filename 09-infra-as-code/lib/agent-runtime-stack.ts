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
 * aws-cdk-lib 2.264.0 の aws-bedrockagentcore モジュールには L1 (CfnRuntime) しか無いため
 * L1 を直接使う。L2 が入ったら移行してよい。
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
    // モデル ID を実行時に差し替えられるようにするため、リソースは foundation-model と
    // inference-profile のワイルドカードにしている。本番では必要な ID に絞ること。
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: [
          `arn:aws:bedrock:${this.region}::foundation-model/*`,
          `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/*`,
          `arn:aws:bedrock:*::foundation-model/*`,
        ],
      }),
    );

    // CloudWatch Logs への出力
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
        resources: [`arn:aws:logs:${this.region}:${this.account}:log-group:/aws/bedrock-agentcore/*`],
      }),
    );

    return role.roleArn;
  }
}
