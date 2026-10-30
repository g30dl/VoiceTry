import os
from collections.abc import Mapping

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI

from voice_chat.app import create_app
from voice_chat.chat import ChatService
from voice_chat.config import Settings
from voice_chat.llm import LLMClient
from voice_chat.tts import TTSClient

# VoiceStudio runs on CPU here, so synthesis can take minutes for long replies.
LLM_TIMEOUT_SECONDS = 60
TTS_TIMEOUT_SECONDS = 600


def build_app(env: Mapping[str, str] | None = None) -> FastAPI:
    if env is None:
        load_dotenv()
        env = os.environ
    settings = Settings.from_env(env)
    llm = LLMClient(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        http=httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS),
    )
    tts = TTSClient(
        base_url=settings.voicestudio_url,
        http=httpx.AsyncClient(timeout=TTS_TIMEOUT_SECONDS),
        voice=settings.voicestudio_voice,
        model="tts-1",
    )
    return create_app(ChatService(llm=llm, tts=tts))
