# 第16章 模範解答

## config.py への追加（「コスト・暴走対策」の節）

```python
    # プロンプトキャッシュ。既定 False の理由: キャッシュ書き込みには割増単価があり、
    # 1 往復で終わる開発中の試行では逆に高くつくことがある。効果はターン数が伸びる
    # 本番ワークロードで出るため、環境ごとに明示的に有効化する
    enable_prompt_cache: bool = False
```

## models.py の変更（全体）

```python
from strands.models import BedrockModel
from strands.models.bedrock import CacheConfig

from ..config import Role, Settings


def build_model(settings: Settings, role: Role) -> BedrockModel:
    kwargs = {}
    if settings.enable_prompt_cache:
        # strategy="auto": キャッシュポイントの配置を Strands に任せる。
        # システムプロンプト・ツール定義が固定（動的な値を含まない）ことがキャッシュ再利用の前提
        kwargs["cache_config"] = CacheConfig(strategy="auto")
    return BedrockModel(
        region_name=settings.aws_region,
        model_id=settings.model_id_for(role),
        max_tokens=settings.max_tokens_for(role),
        **kwargs,
    )
```

## .env.example への追記

```
# プロンプトキャッシュ。書き込み割増があるため開発中は false、
# ターン数の多い本番ワークロードで true にして第13章の eval で前後比較する
ENABLE_PROMPT_CACHE=false
```
