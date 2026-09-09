// 第13章の模範解答。13-guardrails/lib/guardrail-stack.ts として配置する。
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

    // guardrail profile の接頭辞は context から受け取る（既定 us、東京などの ap- リージョンは
    // `-c guardrailProfile=apac`）。リージョン ID をコードに直書きしないため、ARN は
    // スタックのリージョンとアカウントから組み立てる
    const profilePrefix = this.node.tryGetContext('guardrailProfile') ?? 'us';
    const guardrailProfileArn = `arn:${this.partition}:bedrock:${this.region}:${this.account}:guardrail-profile/${profilePrefix}.guardrail.v1:0`;

    const guardrail = new bedrock.CfnGuardrail(this, 'Guardrail', {
      name: 'agent-platform-guardrail',
      // 発動時に利用者へ返る定型文。「何が起きたか」が分かる文にする
      blockedInputMessaging: 'この入力は利用ポリシーによりブロックされました。表現を変えてお試しください。',
      blockedOutputsMessaging: '応答の一部が利用ポリシーによりブロックされました。',
      contentPolicyConfig: {
        filtersConfig: [
          // 既知のプロンプト攻撃パターンをモデルの手前で遮断する。
          // PROMPT_ATTACK は入力側のみのフィルタなので outputStrength は NONE 固定
          { type: 'PROMPT_ATTACK', inputStrength: 'HIGH', outputStrength: 'NONE' },
          { type: 'HATE', inputStrength: 'HIGH', outputStrength: 'HIGH' },
          { type: 'VIOLENCE', inputStrength: 'HIGH', outputStrength: 'HIGH' },
        ],
        // CLASSIC tier は英語・フランス語・スペイン語だけを扱うため、日本語の入力では
        // PROMPT_ATTACK が発動しない。STANDARD tier に切り替える
        contentFiltersTierConfig: { tierName: 'STANDARD' },
      },
      // STANDARD tier は cross-Region の評価が前提。送信元リージョンで使える guardrail profile を渡す
      crossRegionConfig: { guardrailProfileArn },
    });

    // Guardrail は版で参照する。DRAFT を直接使うと、編集が即本番に反映されてしまう
    const version = new bedrock.CfnGuardrailVersion(this, 'GuardrailVersion', {
      guardrailIdentifier: guardrail.attrGuardrailId,
    });

    new CfnOutput(this, 'GuardrailId', { value: guardrail.attrGuardrailId });
    new CfnOutput(this, 'GuardrailVersionNumber', { value: version.attrVersion });
  }
}
