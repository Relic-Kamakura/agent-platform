#!/usr/bin/env node
// 第16章のエントリポイント（編集不要）。3 スタックを定義する。
// リージョンは cdk.json の context から読む（コードにハードコードしない）。
import { App } from 'aws-cdk-lib';
import { NewsKnowledgeBaseStack } from '../lib/knowledge-base-stack';
import { NewsIngestionStack } from '../lib/ingestion-stack';
import { NewsGatewayStack } from '../lib/gateway-stack';

const app = new App();
const region = app.node.tryGetContext('region');
const env = { region };

const kb = new NewsKnowledgeBaseStack(app, 'NewsKnowledgeBaseStack', { env });
new NewsIngestionStack(app, 'NewsIngestionStack', {
  env,
  articleBucket: kb.articleBucket,
  ingestQueue: kb.ingestQueue,
  ingestDlq: kb.ingestDlq,
  knowledgeBaseId: kb.knowledgeBaseId,
  dataSourceId: kb.dataSourceId,
});
new NewsGatewayStack(app, 'NewsGatewayStack', {
  env,
  articleBucket: kb.articleBucket,
  knowledgeBaseId: kb.knowledgeBaseId,
});
app.synth();
