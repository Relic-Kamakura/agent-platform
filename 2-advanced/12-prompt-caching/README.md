# 第12章 プロンプトキャッシュ

この章を終えると、プロンプトキャッシュ付きのエージェントを自分で組み立て、2 回目の呼び出しでキャッシュ読み取りが計上される様子を実測できるようになります。
どんなプロンプト構造なら再利用され、どこを書き換えると再利用されなくなるのかも説明できるようになります。

この章は独立した uv プロジェクトです。最初に依存を入れてください。

```bash
cd 2-advanced/12-prompt-caching
uv sync
```

## 12.1 概要

### 12.1.1 プロンプトキャッシュが解決する問題

モデルの API はステートレスで、エージェントはループを 1 周するたびに、ツール定義とシステムプロンプトと会話履歴の全体を送り直します。
ターンが進むほど、同じ前半部分を毎回全額の課金で処理し直します。

プロンプトキャッシュは、重なる部分の処理結果をモデル側が再利用し、その分を安い単価で課金する仕組みです。

### 12.1.2 どこまでが再利用されるか

Converse API のリクエストは `tools` → `system` → `messages` の順に処理され、キャッシュポイントより手前の並びが前回と一致していれば再利用されます。
手前のセクションを変更すると後ろのセクションのキャッシュが無効になる、と Bedrock のドキュメントにあります。

無効になるのは変更点より後ろのキャッシュポイントだけです。
`system` を書き換えても `tools` のキャッシュポイントは残り、`tools` を変えると `system` と `messages` の両方が無効になります。

エージェントのループでは、各ターンが「前回までの内容 + 新しいツール結果」になります。
前半のツール定義とシステムプロンプトは毎回同じで、そこが再利用されます。
変わる値を手前に置くと再利用されません。
システムプロンプトに現在時刻を埋め込めば毎回 `system` が変わり、ツール定義の順序が実行ごとに変われば `tools` 以降がすべて変わります。

### 12.1.3 課金と最小キャッシュ長

課金は非対称です。
書き込み（初回）は通常の入力より割増、読み取り（2 回目以降）は通常より安くなります。
係数はモデルごとに違うので、Bedrock の料金表で確認してください。
1 往復で終わる呼び出しは割増だけを払うので、有効化すれば必ず安くなるわけではありません。

モデルごとに最小キャッシュ長もあり、キャッシュポイントより手前の合計トークン数がそれに満たないと、エラーにはならず、キャッシュもされません。
既定モデルの最小長は versions.md にあります。
ハンズオンで長い調査ガイドラインを使うのは、この長さを超えるためです。

## 12.2 実装のポイント

Strands では `BedrockModel` に `cache_config` を渡すと有効になります。

```python
from strands.models import BedrockModel, CacheConfig

model = BedrockModel(
    region_name=region_name,
    model_id=model_id,
    max_tokens=1024,
    cache_config=CacheConfig(strategy="auto"),
)
```

`strategy="auto"` は、キャッシュポイントの配置を Strands に任せる指定です。

有効化はこの 1 行ですが、再利用されるかどうかを決めるのはプロンプトの構造のほうです。

再利用されたかどうかは `result.metrics.accumulated_usage` で確認します。
書いたトークン数が `cacheWriteInputTokens`、読んだトークン数が `cacheReadInputTokens` に入ります（キャッシュが動いたときだけ現れるキーです）。

## 12.3 ハンズオン: キャッシュ付きエージェントを組む

長い固定の調査ガイドラインをシステムプロンプトに持つエージェントを組み、同じ質問を 2 回投げてキャッシュの動きを実測します。
編集するのは `exercises/cached_agent.py` の 1 ファイルだけです。

### 12.3.1 TODO を 2 つ埋める

`exercises/cached_agent.py` を開いてください。
システムプロンプト `RESEARCH_GUIDE`（最小キャッシュ長を超える長さの固定文字列）は書いてあり、`build_cached_agent` に TODO が 2 つ残っています。

1. `cache_config=CacheConfig(strategy="auto")` を渡した `BedrockModel` を作る（12.2 のコードの形）
2. その model と `system_prompt=RESEARCH_GUIDE` で `Agent` を組み立てて返す

`RESEARCH_GUIDE` はそのまま渡してください。
現在時刻などを足すと毎回 `system` が変わり、キャッシュが再利用されません（12.1.2）。

### 12.3.2 実行する

同じ質問を 2 回投げ、usage を比べます（このスクリプトは編集しません。Bedrock を呼びます）。

```bash
uv run 01_measure_cache.py
```

1 回目は `cacheWriteInputTokens` にガイドライン分のトークンが計上され、`cacheReadInputTokens` は 0 になります。
2 回目は逆に `cacheReadInputTokens` に計上されます。
2 回目の入力の大部分が、割増の書き込みから安価な読み取りに変わります。

1 回目の `cacheWriteInputTokens` が 0 のときは、本文が最小キャッシュ長（versions.md）に届いていません。
`RESEARCH_GUIDE` に段落を足して伸ばしてから、実行し直してください。

余裕があれば、`RESEARCH_GUIDE` の先頭に 1 文字足して再実行してください。
`system` が変わるため、2 回目もキャッシュ読み取りが 0 のままになります（確認後は元に戻してください）。

<details>
<summary>解答例</summary>

```python
def build_cached_agent(model_id: str, region_name: str) -> Agent:
    """プロンプトキャッシュを有効にしたエージェントを組み立てる。"""
    model = BedrockModel(
        region_name=region_name,
        model_id=model_id,
        max_tokens=1024,
        # strategy="auto": キャッシュポイントの配置を Strands に任せる
        cache_config=CacheConfig(strategy="auto"),
    )
    # RESEARCH_GUIDE をそのまま渡す。現在時刻などを足すと毎回 system が変わり、
    # キャッシュが再利用されない
    return Agent(model=model, system_prompt=RESEARCH_GUIDE)
```

全文は `solutions/cached_agent.py` にあります。

</details>

### 12.3.3 合格判定

TODO コメントを消し、判定を実行します。

```bash
uv run pytest -q
```

`4 passed` で合格です。
モデルは呼ばず、cache_config が渡っていること、引数がそのまま使われていること、ガイドラインが変更なしで渡っていることを検査します。

## 12.4 まとめ

プロンプトキャッシュは、キャッシュポイントより手前の並びが前回と一致した部分だけを安くします。
再利用されるかどうかはプロンプトの構造で決まり、有効化は `cache_config` の 1 行でも、システムプロンプトを固定文字列に保つかどうかで結果が変わります。
効果は `cacheReadInputTokens` の実測で確かめてください。書き込みの割増がある以上、構造が悪ければ有効化がコスト増にもなります。

## 次の章

[第13章 Bedrock Guardrails](../13-guardrails/)
