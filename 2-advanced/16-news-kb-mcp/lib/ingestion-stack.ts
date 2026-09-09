// 取り込みパイプライン（完成品・編集不要）。
// EventBridge Scheduler → Fetch Lambda → S3 → SQS（DLQ 付き）→ Ingest Trigger Lambda → StartIngestionJob。
// 学びの中心は knowledge-base-stack / gateway-stack のハンズオン側にあるため、
// この定型部分は読み比べの対象にする。
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as scheduler from 'aws-cdk-lib/aws-scheduler';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cwactions from 'aws-cdk-lib/aws-cloudwatch-actions';
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { Construct } from 'constructs';
import * as path from 'path';

export interface NewsIngestionStackProps extends cdk.StackProps {
  readonly articleBucket: s3.IBucket;
  readonly ingestQueue: sqs.IQueue;
  readonly ingestDlq: sqs.IQueue;
  readonly knowledgeBaseId: string;
  readonly dataSourceId: string;
}

export class NewsIngestionStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: NewsIngestionStackProps) {
    super(scope, id, props);

    // 処理済み GUID の状態ストア。差分取得（冪等性）の唯一の状態
    const stateTable = new dynamodb.Table(this, 'StateTable', {
      partitionKey: { name: 'guid', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // ハンズオンなので消しやすさ優先
    });

    // RSS を取得して差分だけ S3 に置く Lambda（本体ロジックは exercises と同じ形）
    const fetchFn = new lambda.Function(this, 'FetchFn', {
      runtime: lambda.Runtime.PYTHON_3_13,
      architecture: lambda.Architecture.ARM_64,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda_src/fetch')),
      timeout: cdk.Duration.minutes(5),
      environment: {
        STATE_TABLE: stateTable.tableName,
        ARTICLE_BUCKET: props.articleBucket.bucketName,
      },
    });
    stateTable.grantReadWriteData(fetchFn);
    props.articleBucket.grantPut(fetchFn);

    // 6 時間ごとの起動。間隔は context で変えられる
    const hours = Number(this.node.tryGetContext('scheduleHours') ?? 6);
    const schedulerRole = new iam.Role(this, 'SchedulerRole', {
      assumedBy: new iam.ServicePrincipal('scheduler.amazonaws.com'),
    });
    fetchFn.grantInvoke(schedulerRole);
    new scheduler.CfnSchedule(this, 'FetchSchedule', {
      scheduleExpression: `rate(${hours} hours)`,
      flexibleTimeWindow: { mode: 'OFF' },
      target: { arn: fetchFn.functionArn, roleArn: schedulerRole.roleArn },
    });

    // StartIngestionJob を呼ぶ Lambda。KB あたり同時 1 ジョブの制約があるため、
    // 実行中なら例外にせず、可視性タイムアウトによる再配信に任せる（lambda_src/ingest_trigger）
    const triggerFn = new lambda.Function(this, 'IngestTriggerFn', {
      runtime: lambda.Runtime.PYTHON_3_13,
      architecture: lambda.Architecture.ARM_64,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda_src/ingest_trigger')),
      timeout: cdk.Duration.minutes(1),
      environment: {
        KNOWLEDGE_BASE_ID: props.knowledgeBaseId,
        DATA_SOURCE_ID: props.dataSourceId,
      },
    });
    triggerFn.addEventSource(new SqsEventSource(props.ingestQueue, { batchSize: 10, reportBatchItemFailures: true }));
    triggerFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:StartIngestionJob', 'bedrock:ListIngestionJobs'],
      resources: [
        `arn:aws:bedrock:${this.region}:${this.account}:knowledge-base/${props.knowledgeBaseId}`,
      ],
    }));

    // 失敗の通知。DLQ 滞留と Fetch 失敗をアラームにして SNS へ
    const alarmTopic = new sns.Topic(this, 'AlarmTopic');
    new cloudwatch.Alarm(this, 'DlqAlarm', {
      metric: props.ingestDlq.metricApproximateNumberOfMessagesVisible(),
      threshold: 1,
      evaluationPeriods: 1,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    }).addAlarmAction(new cwactions.SnsAction(alarmTopic));
    new cloudwatch.Alarm(this, 'FetchErrorAlarm', {
      metric: fetchFn.metricErrors({ period: cdk.Duration.hours(1) }),
      threshold: 1,
      evaluationPeriods: 1,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    }).addAlarmAction(new cwactions.SnsAction(alarmTopic));

    new cdk.CfnOutput(this, 'AlarmTopicArn', { value: alarmTopic.topicArn });
    new cdk.CfnOutput(this, 'StateTableName', { value: stateTable.tableName });
  }
}
