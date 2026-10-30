import base64
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from voice_chat.chat import ChatService
from voice_chat.llm import LLMError

INDEX_HTML = Path(__file__).parent / "static" / "index.html"


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)
    length: Literal["short", "medium", "long"]


class ChatResponse(BaseModel):
    reply: str
    audio_b64: str | None
    tts_error: str | None
    llm_ms: int
    tts_ms: int | None


def create_app(chat: ChatService | None = None) -> FastAPI:
    app = FastAPI(title="voice-chat")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return INDEX_HTML.read_text(encoding="utf-8")

    if chat is not None:

        @app.post("/api/chat")
        async def post_chat(request: ChatRequest) -> ChatResponse:
            try:
                result = await chat.reply(request.session_id, request.message, request.length)
            except LLMError as e:
                raise HTTPException(status_code=502, detail=str(e)) from e
            return ChatResponse(
                reply=result.text,
                audio_b64=base64.b64encode(result.audio).decode() if result.audio else None,
                tts_error=result.tts_error,
                llm_ms=result.llm_ms,
                tts_ms=result.tts_ms,
            )

    return app
