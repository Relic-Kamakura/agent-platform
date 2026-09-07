"""設定。環境変数を読む唯一の場所。

他のモジュールから os.environ を直接触らないこと。
リージョン / モデル ID / 各種上限は、すべてここを経由して注入する。
"""

from __future__ import annotations

import functools
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigurationError

Role = Literal["orchestrator", "search", "review"]

# リージョン接頭辞 -> Bedrock 推論プロファイル接頭辞。
# 根拠: strands.models.bedrock._get_default_model_with_warning が使っている対応表と同じ。
# ap-northeast-1 のようにリージョン接頭辞 "ap" と推論プロファイル接頭辞 "apac" がずれるものがある。
_REGION_PREFIX_OVERRIDES = {"ap": "apac"}
# "jp" は国別プロファイルの接頭辞。新しいモデルには地理（apac）ではなく国別（jp）の
# プロファイルしか無いものがある（例: Haiku 4.5。ap-northeast-1 の実機一覧で確認、2026-08-23）。
# その場合は導出に頼らず BEDROCK_MODEL_ID_PREFIX=jp を明示する。
_KNOWN_INFERENCE_PREFIXES = {"us", "eu", "apac", "us-gov", "jp", "global"}


def derive_inference_prefix(region: str) -> str:
    """リージョン名から Bedrock 推論プロファイルの接頭辞を導出する。

    "ap-northeast-1" -> "apac", "us-east-1" -> "us", "us-gov-east-1" -> "us-gov"
    """
    prefix = "-".join(region.split("-")[:-2]).lower()
    return _REGION_PREFIX_OVERRIDES.get(prefix, prefix)


class Settings(BaseSettings):
    """.env と環境変数から読む設定。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- AWS ------------------------------------------------------------
    # 既定 us-east-1: 既定モデル（Haiku 4.5）の推論プロファイルが us. 接頭辞で
    # 実在することを実機の一覧で確認済み（2026-08-23）。
    # 東京（ap-northeast-1）で使う場合は AWS_REGION に加えて BEDROCK_MODEL_ID_PREFIX=jp を
    # 設定する。東京の Haiku 4.5 は apac. ではなく jp. プロファイルのみ（同日実機確認）。
    # AgentCore Runtime 自体は東京でも利用可能（AWS「Supported AWS Regions」表で確認済み）。
    aws_region: str = "us-east-1"

    # --- モデル ID -------------------------------------------------------
    # 未設定ならリージョンから自動導出する（ap-northeast-1 -> "apac"）。
    # オンデマンド直接呼び出しが可能なモデルを使う場合は空文字 "" を明示的に設定する。
    bedrock_model_id_prefix: str | None = None

    # 役割別のベース ID（接頭辞を含まない）。
    #
    # 既定は全役割とも Haiku 4.5。学習時の実行コストを抑えるための割り当てで、
    # Bedrock 単価は入力 $1 / 出力 $5（100万トークンあたり、2026-08 時点）と
    # Sonnet 系（$3 / $15）の 1/3。実案件では判断を伴う orchestrator / review を
    # 上位モデルに差し替える想定で、そのために役割ごとに変数を分けている（第5章）。
    # ID の実在は `./scripts/check_env.sh` が確認する。失敗したら表示される ID に直すこと。
    #
    # 役割ごとの性質（実案件でモデルを割り当て直すときの判断材料）:
    #   orchestrator: 調査観点への分解と、複数の検索結果の統合。判断を伴う（上位モデル候補）。
    #   search:       クエリ整形と検索結果の要約のみ。定型処理なので軽量モデルで足りる。
    #   review:       出力の事実整合・出典有無の検証。見逃しが致命的（上位モデル候補）。
    model_id_orchestrator: str = "anthropic.claude-haiku-4-5-20251001-v1:0"
    model_id_search: str = "anthropic.claude-haiku-4-5-20251001-v1:0"
    model_id_review: str = "anthropic.claude-haiku-4-5-20251001-v1:0"

    # 接頭辞の連結を使わず ID を丸ごと指定したい場合の逃げ道。
    model_id_orchestrator_full: str | None = None
    model_id_search_full: str | None = None
    model_id_review_full: str | None = None

    max_tokens_orchestrator: int = 4096
    max_tokens_search: int = 2048
    max_tokens_review: int = 2048

    # --- コスト・暴走対策 -------------------------------------------------
    # 上限に達したらツールを実行せずエージェントに通知する。デバッグ時も値を上げるだけにし、
    # ガード自体を無効化しないこと。
    max_tool_calls_total: int = Field(default=12, ge=1)
    max_tool_calls_per_tool: int = Field(default=6, ge=1)
    max_agent_turns: int = Field(default=10, ge=1)



    # --- 検索プロバイダ ---------------------------------------------------
    # 既定 mock: API キー無しでローカル実行とテストが完結するようにするため。
    # 実検索には SEARCH_PROVIDER=tavily と TAVILY_API_KEY を設定する。
    search_provider: Literal["mock", "tavily"] = "mock"
    tavily_api_key: str | None = None
    search_max_results: int = Field(default=5, ge=1, le=20)

    # --- 外部 HTTP --------------------------------------------------------
    http_timeout_seconds: float = Field(default=20.0, gt=0)
    http_max_retries: int = Field(default=2, ge=0)

    # --- サーバ -----------------------------------------------------------
    # AgentCore Runtime のコンテナ契約は 0.0.0.0:8080 固定。既定値を変えてはいけない。
    # BedrockAgentCoreApp.run() は host 未指定だと 127.0.0.1 に bind するため明示している。
    # ローカル開発で 8080 が塞がっている場合に限り SERVER_PORT を変更する
    # （macOS では Docker Desktop が 127.0.0.1:8080 を使うことがある）。
    server_host: str = "0.0.0.0"  # noqa: S104 - AgentCore の契約
    server_port: int = 8080

    # --- 運用 -------------------------------------------------------------
    auth_bypass: bool = False
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _validate(self) -> Settings:
        if self.search_provider == "tavily" and not self.tavily_api_key:
            raise ConfigurationError(
                "SEARCH_PROVIDER=tavily には TAVILY_API_KEY が必要です。"
                "キーが無い場合は SEARCH_PROVIDER=mock にしてください。"
            )
        if len(self.aws_region.split("-")) < 3:
            raise ConfigurationError(
                f"AWS_REGION の形式が不正です: {self.aws_region!r}（例: ap-northeast-1）"
            )
        return self

    @property
    def inference_prefix(self) -> str:
        """実際に使う推論プロファイル接頭辞。"""
        if self.bedrock_model_id_prefix is not None:
            return self.bedrock_model_id_prefix.rstrip(".")
        return derive_inference_prefix(self.aws_region)

    def model_id_for(self, role: Role) -> str:
        """役割に対して実際に Bedrock へ渡すモデル ID を返す。"""
        override = getattr(self, f"model_id_{role}_full")
        if override:
            return override
        base = getattr(self, f"model_id_{role}")
        prefix = self.inference_prefix
        return f"{prefix}.{base}" if prefix else base

    def max_tokens_for(self, role: Role) -> int:
        return int(getattr(self, f"max_tokens_{role}"))

    def describe_models(self) -> dict[str, str]:
        """起動時ログ用。何を呼ぼうとしているかを一目で分かるようにする。"""
        return {role: self.model_id_for(role) for role in ("orchestrator", "search", "review")}

    def prefix_warning(self) -> str | None:
        """接頭辞が既知の推論プロファイル接頭辞でない場合の警告文。"""
        prefix = self.inference_prefix
        if prefix and prefix not in _KNOWN_INFERENCE_PREFIXES:
            return (
                f"推論プロファイル接頭辞 {prefix!r} は既知の一覧 {sorted(_KNOWN_INFERENCE_PREFIXES)} "
                "に含まれません。BEDROCK_MODEL_ID_PREFIX で明示するか、"
                "MODEL_ID_*_FULL で ID を丸ごと指定してください。"
            )
        return None


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """プロセス内で 1 度だけ構築する。テストでは cache_clear() してから使う。"""
    return Settings()
