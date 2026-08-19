#!/usr/bin/env node
import { App } from 'aws-cdk-lib';
import { AgentRuntimeStack } from '../lib/agent-runtime-stack';
import { loadConfig } from '../lib/config';
import { EcrStack } from '../lib/ecr-stack';

const app = new App();
const config = loadConfig(app);
const env = { account: config.account, region: config.region };

// ECR と Runtime は別スタック。Runtime 作成時にイメージが存在している必要があるため、
// scripts/deploy.sh が「ECR デプロイ -> push -> Runtime デプロイ」の順で実行する。
new EcrStack(app, 'AgentPlatformEcrStack', config, { env });
new AgentRuntimeStack(app, 'AgentPlatformRuntimeStack', config, { env });

app.synth();
