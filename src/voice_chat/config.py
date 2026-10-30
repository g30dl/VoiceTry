from collections.abc import Mapping
from dataclasses import dataclass


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str
    voicestudio_url: str
    voicestudio_voice: str

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        api_key = env.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ConfigError("OPENROUTER_API_KEY is not set. Add it to your .env file.")
        return cls(
            openrouter_api_key=api_key,
            openrouter_model=env.get("OPENROUTER_MODEL", "google/gemma-3-12b-it"),
            openrouter_base_url=env.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            voicestudio_url=env.get("VOICESTUDIO_URL", "http://127.0.0.1:3900"),
            # A VoiceStudio voice profile: its reference clip keeps the voice stable.
            voicestudio_voice=env.get("VOICESTUDIO_VOICE", "chat-voice"),
        )
