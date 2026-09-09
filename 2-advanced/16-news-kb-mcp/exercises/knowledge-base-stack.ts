// ハンズオン 16.5: S3 Vectors を使う Knowledge Base の定義。
// S3 Vectors / Knowledge Base / DataSource はどれも L2 がまだ無く、L1（Cfn*）で書く。
// プロパティ名は CloudFormation リファレンスと同じ（第18章 18.1.1 の読み方がそのまま使える）。
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

    // 記事バケット（完成済み）。Fetch Lambda が .md と .md.metadata.json を置く
    this.articleBucket = new s3.Bucket(this, 'ArticleBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY, // ハンズオンなので消しやすさ優先
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

    // TODO(1): ベクトルストアを作る。
    //   - s3vectors.CfnVectorBucket（プロパティ指定なしでよい）
    //   - s3vectors.CfnIndex: vectorBucketArn に vectorBucket.attrVectorBucketArn、
    //     dimension に上の dimension、dataType 'float32'、distanceMetric 'cosine'、
    //     metadataConfiguration の nonFilterableMetadataKeys に ['AMAZON_BEDROCK_TEXT']
    //     （KB がチャンク本文をこのキーで metadata に入れるため、フィルタ対象から外す）

    // KB の実行ロール（完成済み）。記事の読み取り、埋め込みモデルの呼び出し、
    // ベクトルストアへの読み書きだけを許可する
    const kbRole = new iam.Role(this, 'KnowledgeBaseRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
    });
    this.articleBucket.grantRead(kbRole);
    kbRole.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: [`arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v2:0`],
    }));
    kbRole.addToPolicy(new iam.PolicyStatement({
      actions: ['s3vectors:*'], // 実機確認後に Put/Query/Get/List へ絞る
      resources: ['*'],
    }));

    // TODO(2): bedrock.CfnKnowledgeBase を作る。
    //   - name / roleArn: kbRole.roleArn
    //   - knowledgeBaseConfiguration: { type: 'VECTOR', vectorKnowledgeBaseConfiguration:
    //       { embeddingModelArn: Titan Text Embeddings V2 の ARN（上の kbRole と同じ ARN 文字列） } }
    //   - storageConfiguration: { type: 'S3_VECTORS', s3VectorsConfiguration:
    //       { indexArn: index.attrIndexArn } }

    // TODO(3): bedrock.CfnDataSource を作り、公開プロパティと CfnOutput を埋める。
    //   - knowledgeBaseId: kb.attrKnowledgeBaseId / name
    //   - dataSourceConfiguration: { type: 'S3', s3Configuration:
    //       { bucketArn: this.articleBucket.bucketArn, inclusionPrefixes: ['news/'] } }
    //   - vectorIngestionConfiguration: { chunkingConfiguration: { chunkingStrategy: 'FIXED_SIZE',
    //       fixedSizeChunkingConfiguration: { maxTokens: 512, overlapPercentage: 20 } } }
    //   - this.knowledgeBaseId = kb.attrKnowledgeBaseId / this.dataSourceId = dataSource.attrDataSourceId
    //   - CfnOutput で KnowledgeBaseId と DataSourceId を出力（16.7 の初回同期で使う）
    this.knowledgeBaseId = '';
    this.dataSourceId = '';
  }
}
