"""QuantPilot 配置管理模块."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，从环境变量或 .env 文件读取."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="QUANTPILOT_",
        case_sensitive=False,
    )

    # 应用基础配置
    app_name: str = "QuantPilot"
    app_version: str = "0.1.0"
    debug: bool = False

    # 数据库配置
    duckdb_path: Path = Path("data/quantpilot.duckdb")
    sqlite_path: Path = Path("data/quantpilot.sqlite")

    # Redis 配置
    redis_url: str = "redis://localhost:6379"

    # API 服务配置
    host: str = "127.0.0.1"
    port: int = 8000

    # 数据目录
    data_dir: Path = Path("data")
    strategy_dir: Path = Path("data/strategies")

    # LLM 配置
    llm_default_model: str = Field(default="gpt-4o", description="默认 LLM 模型")
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    anthropic_api_key: str = Field(default="", description="Anthropic API Key")

    # 日志配置
    log_level: str = "INFO"
    log_dir: Path = Path("logs")


def get_settings() -> Settings:
    """获取全局配置单例."""
    return Settings()
