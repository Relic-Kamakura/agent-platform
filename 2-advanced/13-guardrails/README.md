# 第13章 Bedrock Guardrails

この章を終えると、Guardrail を CDK で定義し、それをモデルに接続したエージェントを組み立てられるようになります。
アプリ側のコードで掛ける上限との役割分担も説明できるようになります。

この章は CDK と uv の 2 つのプロジェクトを持つ独立した章です。最初に両方の依存を入れてください。

```bash
cd 2-advanced/13-guardrails
npm ci
uv sync
```

## 13.1 概要

Bedrock Guardrails は、モデルの入出力を Bedrock の API 側で検査するマネージド機能です。
有害な表現、業務上扱わせたくない話題、PII（氏名やメールアドレスのように個人を特定できる情報）を遮断またはマスクします。

アプリ側のコードで掛ける上限（ツール呼び出し回数やトークン量）が守るのはコストと実行回数です。
Guardrails が守るのは内容で、動く場所も違います。

| | アプリ側のコード | Guardrails |
| --- | --- | --- |
| 守るもの | コストと実行回数 | 有害な内容、PII |
| 動く場所 | プロセス内 | Bedrock の API 側 |
| 発動時 | 理由を返して継続 | 遮断し定型文に置換 |

内容の防御をプロンプトだけに任せない、コストの防御を Guardrails に期待しない、という分担です。

## 13.2 実装のポイント

### 13.2.1 CDK 側で定義するもの

Guardrail 本体はリージョナルなリソースで、ポリシーの集合です。コンテンツフィルタはカテゴリごとに強度付きで遮断し、拒否トピックは自然文で書いた話題を遮断し、機微情報フィルタは PII を遮断またはマスクします。
コンテンツフィルタのカテゴリは HATE / VIOLENCE / SEXUAL / INSULTS / MISCONDUCT / PROMPT_ATTACK の 6 つです。

コンテンツフィルタには tier があり、既定の CLASSIC tier が扱うのは英語とフランス語とスペイン語だけです。日本語の入力では PROMPT_ATTACK が発動しません。
日本語も検査するには `contentFiltersTierConfig` の `tierName` を `STANDARD` にし、STANDARD tier の前提である cross-Region の評価先（`crossRegionConfig` の guardrail profile）を渡します。

Guardrail は版（`CfnGuardrailVersion`）で参照します。DRAFT を直接使うと、編集がそのまま呼び出し側に反映されるからです。

### 13.2.2 アプリ側で渡すもの

Strands では `BedrockModel(..., guardrail_id=..., guardrail_version=...)` のように渡すと接続されます。
両方が揃ったときだけ Converse API に `guardrailConfig` が送られ、片方だけ渡してもエラーにならないまま無視されるので、渡すならセットにします。
どの Guardrail を使うかはコードに書かず、引数（実行時は環境変数）で受け取ります。`guardrail_latest_message` は既定 `False` で、会話に含まれる利用者のメッセージが毎ターン評価対象になるため、長い会話では `True` にして直前の 1 通だけを評価します。

### 13.2.3 Guardrail が評価するもの

| 内容 | 評価 |
| --- | --- |
| 入力プロンプトとモデルの応答 | される |
| システムプロンプト | 囲んだ部分だけ |
| ツール結果とツール引数 | されない |

システムプロンプトが評価されるのは `guardContent` で囲んだ部分だけです。
ツール結果は評価されないため、検索結果に混ざった指示文（間接的なプロンプトインジェクション）は Guardrail では遮断されません。
発動すると `stopReason` が `guardrail_intervened` になり、応答本文が定型文（`blockedInputMessaging` / `blockedOutputsMessaging`）に置き換わります。

呼び出し側の IAM には、guardrail の ARN に加えて `guardrail-profile/<id>` の ARN も要ります。送信元リージョンと、profile が振り分ける全宛先リージョンの `guardrail-profile` ARN を許可します。

`BedrockModel` に `guardrail_id` を渡して評価されるのは、入力と出力だけです。
ツール結果まで検査するなら、bedrock-runtime の `ApplyGuardrail` API を hook（`AfterToolCallEvent`）から呼びます。
`ApplyGuardrail` のタイムアウトや 5xx は遮断扱い（fail-closed）にします。

### 13.2.4 フィルタの強度をどう決めるか

強度は NONE / LOW / MEDIUM / HIGH の 4 段階で、カテゴリごとに入力側と出力側を別々に設定します。
強くするほど有害な入出力を捕まえますが、「A 社の不祥事を調べて」のような業務上まっとうな依頼も巻き込み、止められた利用者には定型文しか見えません。
業務で通ってほしい依頼を 20 件ほど集め、強度を変えながら遮断された件数を数えて決めます。

## 13.3 ハンズオン: Guardrail を CDK で定義する

### 13.3.1 TODO を 5 つ埋める

骨組みをコピーします。編集するのは `lib/guardrail-stack.ts` の 1 ファイルだけです。

```bash
mkdir -p lib && cp exercises/guardrail-stack.ts lib/guardrail-stack.ts
```

`lib/guardrail-stack.ts` を開いてください。`CfnGuardrail` の枠（名前と発動時の定型文）は書いてあり、TODO が 5 つ残っています。
エントリポイント `bin/app.ts` は用意してあり（編集不要）、このファイルを `AgentPlatformGuardrailStack` として読み込みます。

1. `contentPolicyConfig` の `filtersConfig` に `{ type: 'PROMPT_ATTACK', inputStrength: 'HIGH', outputStrength: 'NONE' }` を含める
2. 同じ `contentPolicyConfig` に `contentFiltersTierConfig: { tierName: 'STANDARD' }` を足す
3. `crossRegionConfig` に guardrail profile の ARN を渡す
4. `CfnGuardrailVersion` で版を発行する（`guardrailIdentifier` は `guardrail.attrGuardrailId`）
5. `CfnOutput` で GuardrailId と GuardrailVersionNumber を出力する

PROMPT_ATTACK は入力側だけのフィルタなので、`outputStrength` は `NONE` に固定します。
2 と 3 はセットで要ります。CLASSIC tier のままだと、`01_invoke_guarded.py` が送る日本語の攻撃文に PROMPT_ATTACK が反応しません。STANDARD tier にすると日本語も検査されますが、STANDARD tier は評価を複数リージョンへ振り分ける cross-Region 推論を前提としており、guardrail profile の指定が必須になります。
ARN は `arn:${this.partition}:bedrock:${this.region}:${this.account}:guardrail-profile/${profilePrefix}.guardrail.v1:0` の形で、接頭辞は `this.node.tryGetContext('guardrailProfile') ?? 'us'` で受け取ります（東京などの ap- リージョンは `-c guardrailProfile=apac` を付けて実行します）。

### 13.3.2 実行する

実装できたら TODO コメントを消し、CloudFormation テンプレートに変換します。

```bash
npx cdk synth AgentPlatformGuardrailStack | grep -E 'Bedrock::Guardrail|PROMPT_ATTACK|TierName|GuardrailProfileArn'
```

`AWS::Bedrock::Guardrail` と `AWS::Bedrock::GuardrailVersion`、`PROMPT_ATTACK`、`TierName: STANDARD`、`GuardrailProfileArn` の 5 種類が出るはずです。

<details>
<summary>解答例</summary>

```ts
    const profilePrefix = this.node.tryGetContext('guardrailProfile') ?? 'us';
    const guardrailProfileArn = `arn:${this.partition}:bedrock:${this.region}:${this.account}:guardrail-profile/${profilePrefix}.guardrail.v1:0`;
    // CfnGuardrail の props に足すもの
      contentPolicyConfig: {
        filtersConfig: [{ type: 'PROMPT_ATTACK', inputStrength: 'HIGH', outputStrength: 'NONE' }],
        contentFiltersTierConfig: { tierName: 'STANDARD' },
      },
      crossRegionConfig: { guardrailProfileArn },
    // props の後ろに続けるもの
    const version = new bedrock.CfnGuardrailVersion(this, 'GuardrailVersion', { guardrailIdentifier: guardrail.attrGuardrailId });
    new CfnOutput(this, 'GuardrailId', { value: guardrail.attrGuardrailId });
    new CfnOutput(this, 'GuardrailVersionNumber', { value: version.attrVersion });
```

全文は `solutions/guardrail-stack.ts` にあります。

</details>

### 13.3.3 合格判定

```bash
./verify/verify.sh
```

Guardrail、PROMPT_ATTACK フィルタ、STANDARD tier、guardrail profile、版の発行、CfnOutput の 6 項目が OK になれば合格です。

## 13.4 ハンズオン: モデルに Guardrail をつなぐ

### 13.4.1 TODO を 2 つ埋める

編集するのは `exercises/guarded_model.py` の 1 ファイルだけです。関数のシグネチャは書いてあり、TODO が 2 つ残っています。

1. `guardrail_id` と `guardrail_version` の両方が指定されているときは、それを渡した `BedrockModel` を返す
2. どちらかが None のときは `guardrail_*` を渡さずに返す（接続しない）

### 13.4.2 実行する

実装できたら TODO コメントを消し、組み立てた結果を表示します。

```bash
uv run python -c "import sys; sys.path.insert(0, 'exercises'); from guarded_model import build_guarded_model; c = build_guarded_model(model_id='dummy', region_name='us-east-1', guardrail_id='gr-test', guardrail_version='1').get_config(); print(c['guardrail_id'], c['guardrail_version'])"
```

`gr-test 1` が出るはずです。

<details>
<summary>解答例</summary>

```python
    if guardrail_id and guardrail_version:
        return BedrockModel(region_name=region_name, model_id=model_id,
                            guardrail_id=guardrail_id, guardrail_version=guardrail_version)
    return BedrockModel(region_name=region_name, model_id=model_id)
```

全文は `solutions/guarded_model.py` にあります。

</details>

### 13.4.3 合格判定

```bash
uv run pytest -q
```

`4 passed` で合格です。指定時に id と version の両方がモデルに渡ること、未指定時には渡らないことを検査します。

## 13.5 ハンズオン: 発動を確認する

この節に自動の合格判定はありません。デプロイして応答を目視で確認する工程です。

```bash
npx cdk deploy AgentPlatformGuardrailStack
```

Outputs の GuardrailId と GuardrailVersionNumber を環境変数に入れて、確認スクリプト（編集不要）を実行します。

```bash
GUARDRAIL_ID=<GuardrailId> GUARDRAIL_VERSION=<GuardrailVersionNumber> \
  uv run 01_invoke_guarded.py
```

スクリプトは「これまでの指示はすべて無視して」で始まる日本語の入力を送ります。PROMPT_ATTACK フィルタが入力側で発動し、モデルの回答ではなく `blockedInputMessaging` に書いた定型文が応答に現れるはずです。

## 13.6 まとめ

アプリ側のコードで掛ける上限が実行回数とコストを抑え、Guardrails が内容を止めます。見落としやすいのは言語で、日本語を検査するには STANDARD tier と guardrail profile の指定が要ります。
発動を確認できたら、次は取り消せない操作に人間の承認を挟むゲートを作ります。

## 次の章

[第14章 HITL（承認ゲート）](../14-hitl/)
