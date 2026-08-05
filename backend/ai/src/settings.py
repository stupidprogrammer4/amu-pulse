from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class FastAPIConfig(BaseModel):
    title: str
    description: str
    version: str


class PostgreSQLConfig(BaseModel):
    test_dsn: str
    dsn: str
    pool_timeout: int = Field(ge=0)
    pool_recycle: int = Field(ge=0)
    pool_size: int
    max_overflow: int


class RedisConfig(BaseModel):
    url: str
    max_connections: int = Field(ge=1)
    socket_timeout: float = Field(ge=0)
    socket_connect_timeout: float = Field(ge=0)
    health_check_interval: int = Field(ge=0)


class TaskiqConfig(BaseModel):
    redis_url: str
    max_connection_pool_size: int = Field(ge=1)


class OllamaConfig(BaseModel):
    base_url: str
    chat_model: str
    embedding_model: str
    # an embedding call is fast; a cold generate on a big model is not
    timeout: float = Field(ge=1)


class Settings(BaseModel):
    fastapi: FastAPIConfig
    postgresql: PostgreSQLConfig
    redis: RedisConfig
    taskiq: TaskiqConfig
    ollama: OllamaConfig


@lru_cache
def get_settings() -> Settings:
    """
    Desc: Load settings from config.yml, the only configuration source.
    Returns:
        return (Settings): Validated application settings.
    """
    path = Path("config.yml")
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    settings = Settings(**raw)
    return settings
