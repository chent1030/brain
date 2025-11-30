"""应用配置管理

从环境变量加载所有配置项
支持开发/生产环境配置分离
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """应用配置类

    所有配置从环境变量读取,支持.env文件
    """

    # 应用基础配置
    app_name: str = "Brain AI对话系统"
    env: str = "development"
    debug: bool = True

    # 数据库配置
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/brain_dev"

    # 会话密钥(生产环境必须设置)
    session_secret_key: str = "dev-secret-key-change-in-production"

    # 通义API配置
    tongyi_api_key: str = ""
    tongyi_api_base: str = "https://dashscope.aliyuncs.com/api/v1"

    # MCP服务器配置
    mcp_server_url: str = "http://localhost:3001"
    mcp_server_timeout: int = 5

    # Deep Research配置
    deep_research_timeout: int = 30
    deep_research_max_tokens: int = 4096

    # 数据保留策略(天数)
    data_retention_days: int = 30

    # 日志配置
    log_level: str = "INFO"

    # CORS配置
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """确保数据库URL使用asyncpg驱动"""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """解析CORS允许的源(逗号分隔)"""
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别有效性"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"LOG_LEVEL必须是以下之一: {', '.join(valid_levels)}")
        return upper_v

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.env.lower() == "development"

    def validate_production_config(self) -> None:
        """验证生产环境必需配置

        Raises:
            ValueError: 生产环境缺少必需配置时抛出
        """
        if not self.is_production:
            return

        errors = []

        if self.session_secret_key == "dev-secret-key-change-in-production":
            errors.append(
                "生产环境必须设置SESSION_SECRET_KEY! "
                "生成方法: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

        if not self.tongyi_api_key:
            errors.append("生产环境必须设置TONGYI_API_KEY")

        if self.debug:
            errors.append("生产环境应禁用DEBUG模式(设置DEBUG=False)")

        if errors:
            raise ValueError(
                "生产环境配置验证失败:\n" + "\n".join(f"- {e}" for e in errors)
            )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# 全局配置实例
settings = Settings()


# 启动时验证生产环境配置
if settings.is_production:
    settings.validate_production_config()


# 便捷访问函数
def get_settings() -> Settings:
    """获取配置实例(用于FastAPI依赖注入)

    使用方式:
        @app.get("/endpoint")
        async def endpoint(config: Settings = Depends(get_settings)):
            print(config.app_name)

    Returns:
        Settings: 配置对象
    """
    return settings
