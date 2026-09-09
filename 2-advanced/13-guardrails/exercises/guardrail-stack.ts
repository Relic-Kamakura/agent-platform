// ハンズオン 13.3: Bedrock Guardrail の定義。
// lib/guardrail-stack.ts にコピーして TODO を埋め、`npx cdk synth` で確認する。
// 実装が終わったら TODO コメントは消す。完成形は solutions/guardrail-stack.ts。
import { CfnOutput, Stack, type StackProps } from 'aws-cdk-lib';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import type { Construct } from 'constructs';

/**
 * Bedrock Guardrails（Bedrock の API 側で入出力を検査するマネージド機能）。
 * アプリ側のコードで掛ける回数やトークンの上限とは役割が別で、併用する。
 */
export class GuardrailStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const guardrail = new bedrock.CfnGuardrail(this, 'Guardrail', {
      name: 'agent-platform-guardrail',
      // 発動時に利用者へ返る定型文。「何が起きたか」が分かる文にする
      blockedInputMessaging: 'この入力は利用ポリシーによりブロックされました。表現を変えてお試しください。',
      blockedOutputsMessaging: '応答の一部が利用ポリシーによりブロックされました。',
      // TODO(1): contentPolicyConfig を足す。filtersConfig に少なくとも
      //   { type: 'PROMPT_ATTACK', inputStrength: 'HIGH', outputStrength: 'NONE' }
      //   を含める（PROMPT_ATTACK は入力側のみのフィルタ。outputStrength は NONE 固定）。
      //   HATE / VIOLENCE など他のカテゴリも同じ形で足せる
      // TODO(2): 同じ contentPolicyConfig に contentFiltersTierConfig を足し、
      //   tierName を 'STANDARD' にする。既定の CLASSIC tier は英語・フランス語・
      //   スペイン語だけを扱うため、日本語の入力では PROMPT_ATTACK が発動しない
      // TODO(3): crossRegionConfig に guardrailProfileArn を渡す（STANDARD tier の前提）。
      //   ARN は
      //   `arn:${this.partition}:bedrock:${this.region}:${this.account}:guardrail-profile/<接頭辞>.guardrail.v1:0`
      //   の形。接頭辞は this.node.tryGetContext('guardrailProfile') で受け取り、既定を 'us' にする
    });

    // TODO(4): bedrock.CfnGuardrailVersion で版を発行する。
    //   guardrailIdentifier に guardrail.attrGuardrailId を渡す

    // TODO(5): CfnOutput を 2 つ出す。13.5 で環境変数に入れる値になる。
    //   - GuardrailId: guardrail.attrGuardrailId
    //   - GuardrailVersionNumber: version.attrVersion
  }
}
