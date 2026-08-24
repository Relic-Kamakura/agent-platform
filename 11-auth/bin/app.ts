#!/usr/bin/env node
// 第11章のエントリポイント（編集不要）。
// AuthStack はリージョン非依存のリソースだけなので env の指定は要らない。
import { App } from 'aws-cdk-lib';
import { AuthStack } from '../lib/auth-stack';

const app = new App();
new AuthStack(app, 'AgentPlatformAuthStack');
app.synth();
