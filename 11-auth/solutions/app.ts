#!/usr/bin/env node
// 第11章の模範解答。09-infra-as-code/bin/app.ts の完成形。
import { App } from 'aws-cdk-lib';
import { AgentRuntimeStack } from '../lib/agent-runtime-stack';
import { AuthStack } from '../lib/auth-stack';
import { loadConfig } from '../lib/config';
import { EcrStack } from '../lib/ecr-stack';

const app = new App();
const config = loadConfig(app);
const env = { account: config.account, region: config.region };

// ECR と Runtime は別スタック。Runtime 作成時にイメージが存在している必要があるため、
// scripts/deploy.sh が「ECR デプロイ -> push -> Runtime デプロイ」の順で実行する。
new EcrStack(app, 'AgentPlatformEcrStack', config, { env });

// Cognito（第11章）。Runtime の JWT authorizer と第12章の Route Handler が
// ここのトークンを検証する
const authStack = new AuthStack(app, 'AgentPlatformAuthStack', { env });

new AgentRuntimeStack(app, 'AgentPlatformRuntimeStack', config, {
  env,
  jwtDiscoveryUrl: authStack.discoveryUrl,
  jwtAllowedClients: [authStack.clientId],
});

app.synth();
