import os
import json
from typing import List, Union, Dict, Any, Optional
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "HotLabel User Profiling Service"
    SERVICE_NAME: str = "users-service"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database (Primary: DATABASE_URL, fallback: POSTGRES_* for backward compatibility)
    DATABASE_URL: Optional[str] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/hotlabel_users"
    )

    # Deprecated: Use DATABASE_URL instead. These are kept for backward compatibility.
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_PORT: str = "5432"
    DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        # If DATABASE_URL is set, use it
        db_url = info.data.get("DATABASE_URL")
        if db_url:
            return db_url
        # Otherwise, assemble from POSTGRES_* (deprecated)
        return PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            port=int(info.data.get("POSTGRES_PORT")) if info.data.get("POSTGRES_PORT") is not None else None,
            path=f"{info.data.get('POSTGRES_DB') or ''}",
        )
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: str = "6379"
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Service URLs
    TASKS_SERVICE_URL: AnyHttpUrl
    QA_SERVICE_URL: AnyHttpUrl
    PUBLISHERS_SERVICE_URL: AnyHttpUrl
    
    # User Profiling Settings
    SESSION_EXPIRE_HOURS: int = 24
    ANONYMOUS_DATA_RETENTION_DAYS: int = 30
    EXPERT_LEVEL_THRESHOLDS: List[int] = [10, 50, 100, 250]  # Task counts for each level
    
    @field_validator("EXPERT_LEVEL_THRESHOLDS", mode="before")
    def parse_expert_thresholds(cls, v: Union[str, List[int]]) -> List[int]:
        if isinstance(v, str):
            return json.loads(v)
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
