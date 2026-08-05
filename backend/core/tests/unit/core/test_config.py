from pathlib import Path

from src.core.config import get_settings


def test_yaml_is_the_only_configuration_source(
    monkeypatch,
    tmp_path: Path,
) -> None:
    sample = Path(__file__).parents[3] / "config.yml.sample"
    target = tmp_path / "config.yml"
    target.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "FASTAMU_POSTGRESQL__DSN",
        "postgresql+asyncpg://app:secret@postgres:5432/app",
    )
    monkeypatch.setenv("FASTAMU_REDIS__URL", "redis://redis:6379/0")
    monkeypatch.setenv(
        "FASTAMU_ES__HOSTS",
        '["http://elasticsearch:9200"]',
    )
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.fastapi.title == "AMU Pulse"
    assert settings.postgresql.dsn.endswith("@0.0.0.0:5432/core_pulse_db")
    assert settings.redis.url == "redis://0.0.0.0:6379/0"
    assert settings.es.hosts == ["http://0.0.0.0:9200"]
    get_settings.cache_clear()
