from pathlib import Path

from src.settings import get_settings


def test_yaml_is_the_only_configuration_source(
    monkeypatch,
    tmp_path: Path,
) -> None:
    sample = Path(__file__).parents[1] / "config.yml.sample"
    target = tmp_path / "config.yml"
    target.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("POSTGRESQL__DSN", "postgresql+asyncpg://x@y:5432/z")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.fastapi.title == "AMU Pulse AI"
    assert settings.ollama.base_url == "http://0.0.0.0:11434"
    assert settings.postgresql.dsn.endswith("@0.0.0.0:5432/ai_pulse_db")
    get_settings.cache_clear()
