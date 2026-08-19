"""リージョン名から Bedrock 推論プロファイル ID を解決する（模範解答）。"""

# リージョン接頭辞 -> 推論プロファイル接頭辞の補正表。
# "ap" 系だけプロファイル側は "apac" になる
PREFIX_OVERRIDES = {"ap": "apac"}


def derive_prefix(region: str) -> str:
    """リージョン名から地理接頭辞を導出する。

    "ap-northeast-1" -> "apac" / "us-east-1" -> "us" / "us-gov-east-1" -> "us-gov"
    末尾 2 要素（方角と番号）を落とした残りを接頭辞とし、補正表を通す。
    """
    prefix = "-".join(region.split("-")[:-2]).lower()
    return PREFIX_OVERRIDES.get(prefix, prefix)


def resolve_model_id(base_id: str, region: str, prefix: str | None = None, full: str | None = None) -> str:
    """実際に Bedrock へ渡すモデル ID を組み立てる。

    優先順位: full > prefix（空文字は接頭辞なし）> region からの導出。
    """
    if full:
        return full
    if prefix is None:
        prefix = derive_prefix(region)
    return f"{prefix}.{base_id}" if prefix else base_id


if __name__ == "__main__":
    for region in ("ap-northeast-1", "us-east-1", "eu-central-1", "us-gov-east-1"):
        print(f"{region:16} -> {resolve_model_id('anthropic.claude-haiku-4-5', region)}")
