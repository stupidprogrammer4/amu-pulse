from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class FastAPIConfig(BaseModel):
    title: str
    description: str
    version: str


class TaskiqConfig(BaseModel):
    redis_url: str
    max_connection_pool_size: int


class PostgreSQLConfig(BaseModel):
    test_dsn: str
    dsn: str
    pool_timeout: int = Field(ge=0)
    pool_recycle: int = Field(ge=0)
    pool_size: int
    max_overflow: int


class CryptoConfig(BaseModel):
    encryption_key: str
    password_salt: str


class RedisConfig(BaseModel):
    url: str
    max_connections: int = Field(ge=1)
    socket_timeout: float = Field(ge=0)
    socket_connect_timeout: float = Field(ge=0)
    health_check_interval: int = Field(ge=0)


class JWTConfig(BaseModel):
    algorithm: str
    secret_key: str
    access_token_expire_minutes: int = Field(ge=1)
    # long-lived refresh token; trades for a fresh access token
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 14, ge=1)
    api_secret: str


class StorageConfig(BaseModel):
    path: str
    temp_dir: str
    max_file_size: int = Field(ge=1)
    allowed_extensions: list[str]


class CSRFConfig(BaseModel):
    secret_key: str


class ESConfig(BaseModel):
    hosts: list[str]
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    verify_certs: bool = True
    ca_certs: str | None = None


class Settings(BaseSettings):
    fastapi: FastAPIConfig
    taskiq: TaskiqConfig
    postgresql: PostgreSQLConfig
    crypto: CryptoConfig
    redis: RedisConfig
    jwt: JWTConfig
    storage: StorageConfig
    csrf: CSRFConfig
    es: ESConfig

    model_config = SettingsConfigDict(
        env_prefix="FASTAMU_",
        env_nested_delimiter="__",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Desc: Prefer environment values over YAML values.
        Args:
            settings_cls (type[BaseSettings]): Settings class being loaded.
            init_settings (PydanticBaseSettingsSource): YAML source.
            env_settings (PydanticBaseSettingsSource): Environment source.
            dotenv_settings (PydanticBaseSettingsSource): Dotenv source.
            file_secret_settings (PydanticBaseSettingsSource): Secret source.
        Returns:
            return (tuple[PydanticBaseSettingsSource, ...]): Ordered sources.
        """
        sources = (
            env_settings,
            dotenv_settings,
            init_settings,
            file_secret_settings,
        )
        return sources


@lru_cache
def get_settings() -> Settings:
    """
    Desc: Load YAML settings with environment overrides.
    Returns:
        return (Settings): Validated application settings.
    """
    path = Path("config.yml")
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    settings = Settings(**raw)
    return settings
