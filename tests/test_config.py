import pytest

from voice_chat.config import ConfigError, Settings


def test_from_env_reads_values_and_applies_defaults() -> None:
    settings = Settings.from_env({"OPENROUTER_API_KEY": "k"})

    assert settings.openrouter_api_key == "k"
    assert settings.openrouter_model == "google/gemma-3-12b-it"
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert settings.voicestudio_url == "http://127.0.0.1:3900"
    assert settings.voicestudio_voice == "chat-voice"


def test_from_env_allows_overrides() -> None:
    settings = Settings.from_env(
        {
            "OPENROUTER_API_KEY": "k",
            "OPENROUTER_MODEL": "other/model",
            "VOICESTUDIO_URL": "http://localhost:9999",
        }
    )

    assert settings.openrouter_model == "other/model"
    assert settings.voicestudio_url == "http://localhost:9999"


@pytest.mark.parametrize("env", [{}, {"OPENROUTER_API_KEY": ""}, {"OPENROUTER_API_KEY": "  "}])
def test_from_env_requires_the_api_key(env: dict[str, str]) -> None:
    with pytest.raises(ConfigError, match="OPENROUTER_API_KEY"):
        Settings.from_env(env)
