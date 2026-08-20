// 第11章の模範解答。09-infra-as-code/lib/auth-stack.ts として配置する。
import { CfnOutput, RemovalPolicy, Stack, type StackProps } from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import type { Construct } from 'constructs';

/**
 * Cognito User Pool と App Client。
 * ここが発行するアクセストークンを、Route Handler（第12章）と
 * AgentCore Runtime の JWT authorizer（第11章で配線）の両方が検証する。
 */
export class AuthStack extends Stack {
  public readonly discoveryUrl: string;
  public readonly clientId: string;

  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const pool = new cognito.UserPool(this, 'UserPool', {
      // 社内利用の想定。ユーザは管理者が作る
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      // ひな形なので消しやすさ優先。本番では RETAIN に変えること
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const client = pool.addClient('AppClient', {
      // USER_PASSWORD_AUTH: ハンズオンで CLI からログインするため。
      // 本番の Web アプリでは SRP / Hosted UI を検討する
      authFlows: { userPassword: true },
      generateSecret: false,
    });

    // OIDC の discovery URL。JWT 検証側はここから JWKS の場所を知る
    this.discoveryUrl = `${pool.userPoolProviderUrl}/.well-known/openid-configuration`;
    this.clientId = client.userPoolClientId;

    new CfnOutput(this, 'UserPoolId', { value: pool.userPoolId });
    new CfnOutput(this, 'ClientId', { value: client.userPoolClientId });
    new CfnOutput(this, 'DiscoveryUrl', { value: this.discoveryUrl });
  }
}
