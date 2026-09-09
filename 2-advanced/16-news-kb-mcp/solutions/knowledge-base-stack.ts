// 第16章の模範解答: S3 Vectors を使う Knowledge Base（exercises/knowledge-base-stack.ts の完成形）。
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as s3vectors from 'aws-cdk-lib/aws-s3vectors';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import { Construct } from 'constructs';

export class NewsKnowledgeBaseStack extends cdk.Stack {
  public readonly articleBucket: s3.Bucket;
  public readonly ingestQueue: sqs.Queue;
  public readonly ingestDlq: sqs.Queue;
  public readonly knowledgeBaseId: string;
  public readonly dataSourceId: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.articleBucket = new s3.Bucket(this, 'ArticleBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    });


    // S3 → SQS の追加キュー（完成済み）。通知設定はバケットと同じスタックに置く必要があるため、
    // キューもここに作り、取り込みスタックへ渡す。失敗 4 回で DLQ へ
    this.ingestDlq = new sqs.Queue(this, 'IngestDlq', {
      retentionPeriod: cdk.Duration.days(14),
    });
    this.ingestQueue = new sqs.Queue(this, 'IngestQueue', {
      visibilityTimeout: cdk.Duration.minutes(5),
      deadLetterQueue: { queue: this.ingestDlq, maxReceiveCount: 4 },
    });
    this.articleBucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.SqsDestination(this.ingestQueue),
      { suffix: '.md' }, // metadata.json では起動しない。記事 1 件につき 1 通
    );

    const dimension = Number(this.node.tryGetContext('embeddingDimension') ?? 1024);

    const vectorBucket = new s3vectors.CfnVectorBucket(this, 'VectorBucket');
    const index = new s3vectors.CfnIndex(this, 'VectorIndex', {
      vectorBucketArn: vectorBucket.attrVectorBucketArn,
      dimension,
      dataType: 'float32',
      distanceMetric: 'cosine',
      // KB はチャンク本文を AMAZON_BEDROCK_TEXT キーで metadata に入れる。
      // フィルタ対象の metadata にはサイズ上限があるため、本文はフィルタ対象から外す
      metadataConfiguration: { nonFilterableMetadataKeys: ['AMAZON_BEDROCK_TEXT'] },
    });

    const embeddingModelArn = `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v2:0`;
    const kbRole = new iam.Role(this, 'KnowledgeBaseRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
    });
    this.articleBucket.grantRead(kbRole);
    kbRole.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: [embeddingModelArn],
    }));
    kbRole.addToPolicy(new iam.PolicyStatement({
      actions: ['s3vectors:*'], // 実機確認後に Put/Query/Get/List へ絞る
      resources: ['*'],
    }));

    const kb = new bedrock.CfnKnowledgeBase(this, 'NewsKnowledgeBase', {
      name: 'aws-news-handson',
      roleArn: kbRole.roleArn,
      knowledgeBaseConfiguration: {
        type: 'VECTOR',
        vectorKnowledgeBaseConfiguration: { embeddingModelArn },
      },
      storageConfiguration: {
        type: 'S3_VECTORS',
        s3VectorsConfiguration: { indexArn: index.attrIndexArn },
      },
    });

    const dataSource = new bedrock.CfnDataSource(this, 'NewsDataSource', {
      name: 'aws-news-articles',
      knowledgeBaseId: kb.attrKnowledgeBaseId,
      dataSourceConfiguration: {
        type: 'S3',
        s3Configuration: {
          bucketArn: this.articleBucket.bucketArn,
          inclusionPrefixes: ['news/'],
        },
      },
      vectorIngestionConfiguration: {
        chunkingConfiguration: {
          chunkingStrategy: 'FIXED_SIZE',
          fixedSizeChunkingConfiguration: { maxTokens: 512, overlapPercentage: 20 },
        },
      },
    });

    this.knowledgeBaseId = kb.attrKnowledgeBaseId;
    this.dataSourceId = dataSource.attrDataSourceId;

    new cdk.CfnOutput(this, 'KnowledgeBaseId', { value: this.knowledgeBaseId });
    new cdk.CfnOutput(this, 'DataSourceId', { value: this.dataSourceId });
  }
}
