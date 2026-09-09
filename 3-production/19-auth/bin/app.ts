#!/usr/bin/env node
// 第19章のエントリポイント（編集不要）。
// env を指定していないので、User Pool は CDK_DEFAULT_REGION（または --profile のリージョン）
// に作られる。Cognito User Pool はリージョナルなリソースで、作った後にリージョンは変えられない。
import { App } from 'aws-cdk-lib';
import { AuthStack } from '../lib/auth-stack';

const app = new App();
new AuthStack(app, 'AgentPlatformAuthStack');
app.synth();
