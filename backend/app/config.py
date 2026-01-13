"""
HL-OS 配置管理模块
使用 Pydantic Settings 管理所有环境变量和配置
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用程序配置"""

    # =============================================================================
    # 应用配置
    # =============================================================================
    ENVIRONMENT: str = Field(default="development", description="运行环境")
    DEBUG: bool = Field(default=False, description="调试模式")
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")

    # =============================================================================
    # 服务器配置
    # =============================================================================
    BACKEND_HOST: str = Field(default="0.0.0.0", description="后端服务主机")
    BACKEND_PORT: int = Field(default=8000, description="后端服务端口")
    FRONTEND_PORT: int = Field(default=8501, description="前端服务端口")

    # =============================================================================
    # 安全配置
    # =============================================================================
    SECRET_KEY: str = Field(..., description="应用密钥")
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:8501,http://localhost:3000",
        description="允许的CORS源（逗号分隔）"
    )
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API密钥请求头")
    PARENT_API_KEY: Optional[str] = Field(default=None, description="家长API密钥")

    # =============================================================================
    # 外部API密钥
    # =============================================================================
    GOOGLE_AI_STUDIO_API_KEY: str = Field(..., description="Google AI Studio API密钥")
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API密钥")

    # Gemini模型配置
    GEMINI_MODEL: str = Field(
        default="gemini-3-pro-preview-11-2025",
        description="Gemini 3 Pro Preview 视觉识别模型"
    )

    # Claude模型配置
    CLAUDE_MODEL_TEACHING: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude Sonnet 4.5 教学内容生成模型"
    )
    CLAUDE_MODEL_GRADING: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude Sonnet 4.5 批改模型"
    )

    # =============================================================================
    # AnythingLLM配置
    # =============================================================================
    ANYTHINGLLM_URL: str = Field(
        default="http://anythingllm:3001",
        description="AnythingLLM服务地址"
    )
    ANYTHINGLLM_API_KEY: Optional[str] = Field(
        default=None,
        description="AnythingLLM API密钥"
    )

    # =============================================================================
    # Obsidian配置
    # =============================================================================
    OBSIDIAN_VAULT_PATH: str = Field(
        default="/app/obsidian_vault",
        description="Obsidian vault路径"
    )

    # =============================================================================
    # 文件存储配置
    # =============================================================================
    UPLOAD_DIR: str = Field(default="/app/uploads", description="上传文件目录")
    MAX_UPLOAD_SIZE: int = Field(default=10485760, description="最大上传大小(字节)")
    ALLOWED_IMAGE_TYPES: str = Field(
        default="image/jpeg,image/png,image/jpg",
        description="允许的图片类型"
    )

    # =============================================================================
    # 数据库配置
    # =============================================================================
    DATABASE_URL: str = Field(
        default="sqlite:///./hlos.db",
        description="数据库连接URL"
    )

    # =============================================================================
    # Redis配置
    # =============================================================================
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        description="Redis连接URL"
    )

    # =============================================================================
    # 备份配置
    # =============================================================================
    BACKUP_ENABLED: bool = Field(default=True, description="是否启用备份")
    BACKUP_SCHEDULE: str = Field(default="0 2 * * *", description="备份计划(Cron)")
    BACKUP_RETENTION_DAYS: int = Field(default=30, description="备份保留天数")
    BACKUP_DESTINATION: str = Field(default="/backups", description="备份目标路径")

    # =============================================================================
    # 速率限制配置
    # =============================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用速率限制")
    GEMINI_RPM: int = Field(default=50, description="Gemini请求/分钟")
    CLAUDE_RPM: int = Field(default=40, description="Claude请求/分钟")

    # =============================================================================
    # AnythingLLM内部配置
    # =============================================================================
    VECTOR_DB: str = Field(default="lancedb", description="向量数据库类型")
    LLM_PROVIDER: str = Field(default="generic-openai", description="LLM提供商")
    GENERIC_OPEN_AI_BASE_PATH: str = Field(
        default="https://api.anthropic.com/v1",
        description="OpenAI兼容API基础路径"
    )
    GENERIC_OPEN_AI_MODEL_PREF: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="默认LLM模型（AnythingLLM使用）"
    )
    EMBEDDING_ENGINE: str = Field(default="native", description="嵌入引擎")
    EMBEDDING_MODEL_PREF: str = Field(
        default="nomic-embed-text",
        description="嵌入模型"
    )

    # =============================================================================
    # Pydantic设置配置
    # =============================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    # =============================================================================
    # 验证器
    # =============================================================================
    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> List[str]:
        """解析允许的CORS源"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_IMAGE_TYPES")
    @classmethod
    def parse_allowed_image_types(cls, v: str) -> List[str]:
        """解析允许的图片类型"""
        if isinstance(v, str):
            return [img_type.strip() for img_type in v.split(",")]
        return v

    # =============================================================================
    # 辅助方法
    # =============================================================================
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.ENVIRONMENT.lower() == "development"

    def get_cors_origins(self) -> List[str]:
        """获取CORS允许的源列表"""
        if isinstance(self.ALLOWED_ORIGINS, list):
            return self.ALLOWED_ORIGINS
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """获取设置单例（使用缓存）"""
    return Settings()


# 导出全局设置实例
settings = get_settings()
