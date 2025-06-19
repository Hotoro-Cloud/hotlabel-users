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
    SECRET_KEY: Optional[str]
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
    
    DATABASE_URL: Optional[str] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/hotlabel_users"
    )
    
    # Redis
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://redis:6379/0")
    REDIS_HOST: Optional[str]

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
        extra = "ignore"  # Allow extra fields from environment


settings = Settings()
