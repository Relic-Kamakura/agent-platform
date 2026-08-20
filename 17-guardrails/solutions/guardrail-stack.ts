// 第17章の模範解答。09-infra-as-code/lib/guardrail-stack.ts として配置する。
import { CfnOutput, Stack, type StackProps } from 'aws-cdk-lib';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import type { Construct } from 'constructs';

/**
 * Bedrock Guardrails（マネージド層の内容フィルタ）。
 * アプリ層のガード（第4章の hooks）とは役割が別で、併用する。
 */
export class GuardrailStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const guardrail = new bedrock.CfnGuardrail(this, 'Guardrail', {
      name: 'agent-platform-guardrail',
      // 発動時に利用者へ返る定型文。「何が起きたか」が分かる文にする
      blockedInputMessaging: 'この入力は利用ポリシーによりブロックされました。表現を変えてお試しください。',
      blockedOutputsMessaging: '応答の一部が利用ポリシーによりブロックされました。',
      contentPolicyConfig: {
        filtersConfig: [
          // 既知のプロンプト攻撃パターンをモデルの手前で遮断（第14章の多層防御の一層）。
          // PROMPT_ATTACK は入力側のみのフィルタなので outputStrength は NONE 固定
          { type: 'PROMPT_ATTACK', inputStrength: 'HIGH', outputStrength: 'NONE' },
          { type: 'HATE', inputStrength: 'HIGH', outputStrength: 'HIGH' },
          { type: 'VIOLENCE', inputStrength: 'HIGH', outputStrength: 'HIGH' },
        ],
      },
    });

    // Guardrail は版で参照するのが実務の型。DRAFT を直接使うと、編集が即本番に反映されてしまう
    const version = new bedrock.CfnGuardrailVersion(this, 'GuardrailVersion', {
      guardrailIdentifier: guardrail.attrGuardrailId,
    });

    new CfnOutput(this, 'GuardrailId', { value: guardrail.attrGuardrailId });
    new CfnOutput(this, 'GuardrailVersionNumber', { value: version.attrVersion });
  }
}
