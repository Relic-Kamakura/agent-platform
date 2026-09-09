// ハンズオン 16.5: S3 Vectors を使う Knowledge Base の定義。
// S3 Vectors / Knowledge Base / DataSource には aws-cdk-lib 本体に L1（Cfn*）だけがあるので、
// L1 で書く。L1 のプロパティ名は CloudFormation リファレンスの記載と 1 対 1 で対応する。
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
    // キューもここに作り、取り込みスタックへ渡す。取り込みジョブの実行中は
    // Ingest Trigger がバッチ全件を失敗として返すので、可視性タイムアウト 5 分 ×
    // maxReceiveCount 12 = 約 60 分ぶんの再配信を許し、ジョブ 1 回が終わるのを待てるようにする
    this.ingestDlq = new sqs.Queue(this, 'IngestDlq', {
      retentionPeriod: cdk.Duration.days(14),
    });
    this.ingestQueue = new sqs.Queue(this, 'IngestQueue', {
      visibilityTimeout: cdk.Duration.minutes(5),
      deadLetterQueue: { queue: this.ingestDlq, maxReceiveCount: 12 },
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
    //       { embeddingModelArn: Titan Text Embeddings V2 の ARN（上の kbRole と同じ ARN 文字列）,
    //         embeddingModelConfiguration: { bedrockEmbeddingModelConfiguration:
    //           { dimensions: 上の dimension, embeddingDataType: 'FLOAT32' } } } }
    //     （Titan V2 は 1024 / 512 / 256 を出し分けられる。CfnIndex の dimension と
    //       食い違うと取り込みが失敗するので、同じ値を両方に渡す）
    //   - storageConfiguration: { type: 'S3_VECTORS', s3VectorsConfiguration:
    //       { indexArn: index.attrIndexArn } }

    // TODO(3): bedrock.CfnDataSource を作り、公開プロパティと CfnOutput を埋める。
    //   - knowledgeBaseId: kb.attrKnowledgeBaseId / name
    //   - dataSourceConfiguration: { type: 'S3', s3Configuration:
    //       { bucketArn: this.articleBucket.bucketArn, inclusionPrefixes: ['news/'] } }
    //   - vectorIngestionConfiguration: { chunkingConfiguration: { chunkingStrategy: 'FIXED_SIZE',
    //       fixedSizeChunkingConfiguration: { maxTokens: 512, overlapPercentage: 20 } } }
    //   - this.knowledgeBaseId = kb.attrKnowledgeBaseId / this.dataSourceId = dataSource.attrDataSourceId
    //   - CfnOutput で KnowledgeBaseId と DataSourceId を出力（16.6 の初回同期で使う）
    this.knowledgeBaseId = '';
    this.dataSourceId = '';
  }
}
