import pytest
from eleven_blog_tunner.core.config import Settings, get_settings, get_project_root
from pathlib import Path

class TestConfig:
    def test_settings_default_values(self):
        settings = Settings()
        assert settings.llm_provider == "openai"
        assert settings.llm_model == "gpt-4"
        assert settings.llm_temperature == 0.7
        assert settings.llm_max_tokens == 4096

    def test_settings_custom_values(self):
        settings = Settings(
            llm_provider="claude",
            llm_model="claude-3-sonnet"
        )
        assert settings.llm_provider == "claude"
        assert settings.llm_model == "claude-3-sonnet"

    def test_settings_environment_override(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "custom_provider")
        settings = Settings()
        assert settings.llm_provider == "custom_provider"

    def test_settings_database_url(self):
        settings = Settings()
        assert hasattr(settings, 'database_url')
        assert settings.database_url.startswith("sqlite")

    def test_settings_rag_defaults(self):
        settings = Settings()
        assert settings.chunk_size == 1000
        assert settings.chunk_overlap == 200
        assert settings.embedding_model == "text-embedding-3-small"

    def test_settings_log_level(self):
        settings = Settings()
        assert settings.log_level == "INFO"


class TestGetSettings:
    def test_get_settings_returns_singleton(self):
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_returns_settings_instance(self):
        settings = get_settings()
        assert isinstance(settings, Settings)


class TestProjectRoot:
    def test_get_project_root_returns_path(self):
        root = get_project_root()
        assert isinstance(root, Path)

    def test_get_project_root_has_pyproject(self):
        root = get_project_root()
        assert (root / "pyproject.toml").exists()
