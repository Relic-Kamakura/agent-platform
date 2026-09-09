# 第1章 Bedrock で Claude を呼び出す

この章を終えると、Bedrock の Converse API を SDK から直接呼べるようになり、1 回の呼び出しの料金を usage から概算でき、同期とストリーミングの応答の差を実測した状態になります。

この章は独立した uv プロジェクトです。
最初に依存を入れてください。

```bash
cd 1-basic/01-invoke-bedrock
uv sync
```

ハンズオンは `exercises/` の TODO を実装して実行する形式で、完成形は `solutions/` にあります。
AWS の認証情報は設定済みであることを前提にします。

## 1.1 概要

### 1.1.1 Bedrock とは

Amazon Bedrock は、複数ベンダーの基盤モデル（Anthropic Claude、Amazon Nova、Meta Llama など）を単一の API で呼び出せる AWS のフルマネージドサービスです。
呼び出し権限は IAM で管理するので、API キーの配布と失効管理が要りません。
入出力はモデルの学習に使われず（[Bedrock の FAQ](https://aws.amazon.com/bedrock/faqs/)）、CloudTrail や CloudWatch で監査と監視ができます。

### 1.1.2 Converse API

モデル呼び出しには Converse API を使います。
モデルごとに異なるリクエスト形式を統一した層なので、モデルの乗り換えが `modelId` の差し替えだけで済みます。
`messages` は `role`（user / assistant）と `content` の配列で、会話履歴もここに積みます。
`inferenceConfig` は生成の制御、レスポンスは `output` に応答本文、`usage` に消費トークン数です。

```python
response = client.converse(
    modelId="<推論プロファイル ID>",
    messages=[
        {"role": "user", "content": [{"text": "質問文"}]},
    ],
    inferenceConfig={"maxTokens": 300},
)

response["output"]["message"]["content"][0]["text"]  # 応答本文
response["usage"]  # {"inputTokens": ..., "outputTokens": ..., ...}
```

`inferenceConfig` に入る値のうち、この章で使うのは `maxTokens` だけです。

| パラメータ | 何を決めるか |
| --- | --- |
| `maxTokens` | 出力の上限トークン数 |
| `temperature` | 語を選ぶときのばらつき |
| `topP` | 候補を残す確率の割合 |
| `stopSequences` | 生成を打ち切る文字列 |

`temperature` と `topP` は両方動かすと影響を切り分けられないので、片方だけを動かします。

### 1.1.3 出力が上限で切れたとき

1 回の呼び出しには、入力と出力を合わせたコンテキストウィンドウと、出力側だけに掛かる最大出力の 2 つの上限があります（値は docs/versions.md）。
総枠を超えると呼び出しが例外になりますが、`maxTokens` に達しても例外は出ず、文の途中で切れた応答が正常なレスポンスとして返ります。

```python
response["stopReason"]  # "end_turn" なら生成しきった。"max_tokens" なら途中で切れた
```

`stopReason` を見ずに応答を JSON としてパースすると、パースに失敗します。

### 1.1.4 トークンと料金

モデルは文章をトークンという単位に分割して処理し、課金もこの単位です。
単価はモデルとリージョンごとに決まり、出力は入力より数倍高くなっています（docs/versions.md）。

```python
cost = usage["inputTokens"] * 入力単価 / 1_000_000 + usage["outputTokens"] * 出力単価 / 1_000_000
```

長いシステムプロンプト、積み上がる会話履歴、冗長な出力が、そのまま金額になります。

### 1.1.5 同期とストリーミング

`converse` は全文を一括で受け取り、`converse_stream` は断片を順に受け取ります。
引数は同じで、受け取り側だけがループになります。

```python
response = client.converse_stream(...)  # 引数は converse と同じ

for event in response["stream"]:
    if "contentBlockDelta" in event:
        event["contentBlockDelta"]["delta"]["text"]  # 本文の断片
    elif "metadata" in event:
        event["metadata"]["usage"]  # 消費トークン。最後に 1 回だけ届く
```

同期は全文が完成するまで無応答なので、生成に 20 秒かかれば 20 秒無言になります。
体感を決めるのは、この最初の 1 文字までの時間です。

### 1.1.6 クロスリージョン推論プロファイル

新しめの Claude は、クロスリージョン推論プロファイル経由でしか呼べないものが多くなっています。
ID は接頭辞 + モデル ID（地理の `us.` / `apac.` / `eu.` のほか、`global.` と国別の `jp.` もある）で、リクエストは同一地理内の宛先リージョンへ自動ルーティングされます。
追加料金はなく、課金は呼び出し元リージョンの単価です。
接頭辞はリージョン名から機械的に切り出せない（ap-northeast-1 は `ap` ではなく `apac`）ので、使いたいモデルにどの接頭辞があるかは 1.3 の一覧コマンドで確認します。

## 1.2 実装のポイント

このリポジトリが Bedrock 呼び出しに課す規約は 3 つです。

モデル ID とリージョンはコードに書きません。
`.env` を読む設定クラスを 1 か所だけ置き、地理接頭辞の連結もそこで行います（本体では `07-full-app/src/config.py`）。
ID の差し替えだけでモデルを乗り換えられる状態を保つためです。

消費トークンは必ずログに出します。
`response["usage"]` を積み上げたものが、上限値を決めるときの実測データになります。

クライアントには読み取りタイムアウトと自動リトライの設定を渡します。
既定のままだと、長い生成が読み取りタイムアウトで切れたときに botocore が同じリクエストを自動で再送し、同じ生成が二重に走ります（課金も二重）。
`boto3.client("bedrock-runtime", config=Config(read_timeout=150, retries={"max_attempts": 1}))`で自動再送を止め、失敗は失敗として扱います。

## 1.3 ハンズオン: 呼べるモデル ID を確認する

ID を間違えると `ValidationException` が返りますが、接頭辞が違うのかモデルが無いのかは例外からは区別できません。
そのためコードを書く前に、自分のリージョンで呼べる ID の一覧を確認します。

```bash
aws bedrock list-inference-profiles --region us-east-1 \
  --query 'inferenceProfileSummaries[].inferenceProfileId' | grep anthropic
```

`--region` は自分のリージョンに合わせてください。
呼べる ID の一覧が出るはずです。
以降のハンズオンではこの一覧にある ID を使います。
なお、コンソールの Model access で未申請の場合は `AccessDeniedException` になります。
ValidationException とは別物です。

リポジトリ直下の `scripts/check_env.sh` はこの確認を自動化したもので、`.env` の値が一覧に無ければ起動前に止めます。

## 1.4 ハンズオン: Converse API を呼ぶ

### 1.4.1 TODO を 3 個埋める

`exercises/01_converse.py` を開いてください。
クライアントの生成とモデル ID の解決は書いてあり、TODO が 3 つ残っています。

1. `client.converse` の呼び出し。`messages` と `inferenceConfig` の形式は 1.1.2 のとおり
2. 応答テキストの表示。本文は `response["output"]["message"]["content"]` の先頭要素
3. 消費トークンの表示。`response["usage"]` に入っている

### 1.4.2 実行する

実装できたら TODO コメントを消して実行します。

```bash
uv run exercises/01_converse.py
```

既定値（us-east-1 / Haiku 4.5）と自分の環境が違う場合は、環境変数で上書きします。

```bash
AWS_REGION=<リージョン> MODEL_ID=<1.3 で確認した ID> uv run exercises/01_converse.py
```

応答テキストが 1〜2 行と、`tokens: in=... out=...` が表示されるはずです。

<details>
<summary>解答例</summary>

```python
response = client.converse(
    modelId=model_id,
    messages=[
        {"role": "user", "content": [{"text": "こんにちは。1 行で自己紹介して"}]},
    ],
    inferenceConfig={"maxTokens": 300},
)

print(response["output"]["message"]["content"][0]["text"])

usage = response["usage"]
print(f"tokens: in={usage['inputTokens']} out={usage['outputTokens']}")
```

全文は `solutions/01_converse.py` にあります。

</details>

## 1.5 ハンズオン: トークンを数えて料金を出す

### 1.5.1 TODO を 2 個埋める

1.4 で表示した `usage` が料金の実データです。
`exercises/02_count_tokens.py` を開いてください。
呼び出し部分は書いてあり、TODO が 2 つ残っています。

1. 1 回分の料金の計算。式は 1.1.4 のとおりで、ファイル冒頭の単価は 100万トークンあたりの USD
2. 長さの違う 3 つの質問。一語で答えられるものから、長い説明を求めるものまで

### 1.5.2 実行する

実装できたら TODO コメントを消して実行します。

```bash
uv run exercises/02_count_tokens.py
```

3 行の結果が出るはずです。
入力トークンの差は数十程度なのに、出力トークンの差で料金が 1 桁変わります。
入力より単価の高い出力をどれだけ絞れるかが、コストの大半を決めます。

<details>
<summary>解答例</summary>

```python
    cost = usage["inputTokens"] * PRICE_INPUT / 1_000_000 + usage["outputTokens"] * PRICE_OUTPUT / 1_000_000
    print(f"in={usage['inputTokens']:4} out={usage['outputTokens']:4} cost=${cost:.6f} <- {text}")


ask("1+1 は？答えだけ")
ask("エージェント開発を学ぶ手順を 3 項目で")
ask("エージェント開発を学ぶ手順を詳しく説明して")
```

全文は `solutions/02_count_tokens.py` にあります。

</details>

## 1.6 ハンズオン: ストリーミングで呼ぶ

### 1.6.1 TODO を 3 個埋める

同期との違いである、最初の文字が出るまでの時間を実測します。
`exercises/03_streaming.py` を開いてください。
時間計測の枠は書いてあり、TODO が 3 つ残っています。

1. `converse_stream` での呼び出し。引数は `converse` と同じ
2. `contentBlockDelta` イベントのテキストを逐次表示し、最初のチャンクの経過時間を `first_token_at` に記録する
3. `metadata` イベントから `usage` を取り出す。消費トークンは最後にまとめて届く

### 1.6.2 実行する

実装できたら TODO コメントを消して実行します。

```bash
uv run exercises/03_streaming.py
```

文章が少しずつ表示され、最後に 2 つの時間が出るはずです。

```
first_token=0.62s total=6.31s
tokens: in=21 out=498
```

total が数秒かかっても、first_token はその何分の一かです。
この差がそのまま体感の差になります。

<details>
<summary>解答例</summary>

```python
response = client.converse_stream(
    modelId=model_id,
    messages=[
        {"role": "user", "content": [{"text": "エージェント開発を学ぶ手順を詳しく説明して"}]},
    ],
    inferenceConfig={"maxTokens": 500},
)

for event in response["stream"]:
    if "contentBlockDelta" in event:
        if first_token_at is None:
            first_token_at = time.perf_counter() - start
        print(event["contentBlockDelta"]["delta"]["text"], end="", flush=True)
    elif "metadata" in event:
        usage = event["metadata"]["usage"]
```

全文は `solutions/03_streaming.py` にあります。

</details>

### 1.6.3 合格判定

```bash
uv run pytest -q
```

`3 passed` で合格です。
詰まったら `solutions/` を見てください。

## 1.7 まとめ

Converse API は、モデルが違っても `messages` と `inferenceConfig` と `usage` の3 つで呼べるようにする層です。
1 回の料金は `usage` の入出力トークン数から計算でき、1.5 で見たとおり金額を決めるのは出力の長さです。
同期とストリーミングの差は最初の 1 文字が出るまでの時間に現れ、1.6 の first_token と total の開きがそれです。

呼ぶ前に ID の実在を確認し、呼んだ後に usage を見る。
この 2 つが、この先すべてのモデル呼び出しの前提になります。

## 次の章

[第2章 はじめてのエージェント](../02-agent-loop/)
