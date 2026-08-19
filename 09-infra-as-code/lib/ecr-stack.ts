import { CfnOutput, RemovalPolicy, Stack, type StackProps } from 'aws-cdk-lib';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import type { Construct } from 'constructs';
import type { PlatformConfig } from './config';

/**
 * ECR リポジトリだけを持つスタック。
 *
 * Runtime スタックと分けているのは、AgentCore Runtime の作成時に
 * イメージが既に push されている必要があるため。
 * 同一スタックで作ると「空の ECR を参照する Runtime」を作ろうとして失敗する。
 * デプロイ順序は scripts/deploy.sh が強制する。
 */
export class EcrStack extends Stack {
  public readonly repository: ecr.Repository;

  constructor(scope: Construct, id: string, config: PlatformConfig, props?: StackProps) {
    super(scope, id, props);

    this.repository = new ecr.Repository(this, 'AgentRepository', {
      repositoryName: config.ecrRepositoryName,
      imageScanOnPush: true,
      // ひな形なので destroy を既定にする。本番運用では RETAIN に変えること。
      removalPolicy: RemovalPolicy.DESTROY,
      emptyOnDelete: true,
      lifecycleRules: [{ maxImageCount: 10, description: 'Keep only the 10 most recent images' }],
    });

    new CfnOutput(this, 'RepositoryUri', {
      value: this.repository.repositoryUri,
      description: 'Target URI for docker push',
      exportName: `${this.stackName}-RepositoryUri`,
    });
  }
}
