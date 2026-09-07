#!/usr/bin/env node
// 第17章のエントリポイント（編集不要）。
import { App } from 'aws-cdk-lib';
import { GuardrailStack } from '../lib/guardrail-stack';

const app = new App();
new GuardrailStack(app, 'AgentPlatformGuardrailStack');
app.synth();
