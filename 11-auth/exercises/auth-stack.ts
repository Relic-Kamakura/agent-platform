// ハンズオン 11.3: Cognito User Pool と App Client。
// lib/auth-stack.ts にコピーして TODO を埋め、`npx cdk synth` で確認する。
// 実装が終わったら TODO コメントは消す。完成形は solutions/auth-stack.ts。
import { CfnOutput, RemovalPolicy, Stack, type StackProps } from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import type { Construct } from 'constructs';

/**
 * Cognito User Pool と App Client。
 * ここが発行するアクセストークンを、Route Handler（第12章）と
 * AgentCore Runtime の JWT authorizer の両方が検証する。
 */
export class AuthStack extends Stack {
  public readonly discoveryUrl: string;
  public readonly clientId: string;

  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // TODO(1): cognito.UserPool を作る。
    //   - selfSignUpEnabled: false（社内利用。ユーザは管理者が作る）
    //   - signInAliases: { email: true }
    //   - removalPolicy: RemovalPolicy.DESTROY（ひな形なので消しやすさ優先）

    // TODO(2): pool.addClient() で App Client を作る。
    //   - authFlows: { userPassword: true }（11.4 で CLI からログインするため）
    //   - generateSecret: false

    // TODO(3): 次の 2 行を書き換えて実値を入れる。
    //   - discoveryUrl は pool.userPoolProviderUrl に
    //     '/.well-known/openid-configuration' を連結して組み立てる（11.1.3）
    //   - clientId は client.userPoolClientId
    this.discoveryUrl = '';
    this.clientId = '';

    // TODO(4): CfnOutput を 3 つ出す。
    //   - UserPoolId: pool.userPoolId
    //   - ClientId: this.clientId
    //   - DiscoveryUrl: this.discoveryUrl
  }
}
