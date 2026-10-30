import base64

import httpx
import pytest

from tests.fakes import FakeLLM, FakeTTS
from voice_chat.app import create_app
from voice_chat.chat import ChatService
from voice_chat.llm import LLMError


def make_client(llm: FakeLLM | None = None, tts: FakeTTS | None = None) -> httpx.AsyncClient:
    chat = ChatService(llm=llm or FakeLLM(reply="Hola!"), tts=tts or FakeTTS(audio=b"wav"))
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(chat)), base_url="http://test"
    )


PAYLOAD = {"session_id": "s1", "message": "Hola", "length": "short"}


async def test_chat_returns_text_audio_and_timings() -> None:
    async with make_client() as client:
        response = await client.post("/api/chat", json=PAYLOAD)

    body = response.json()
    assert response.status_code == 200
    assert body["reply"] == "Hola!"
    assert base64.b64decode(body["audio_b64"]) == b"wav"
    assert body["tts_error"] is None
    assert body["llm_ms"] >= 0
    assert body["tts_ms"] >= 0


async def test_chat_returns_null_audio_when_voice_fails() -> None:
    from voice_chat.tts import TTSError

    async with make_client(tts=FakeTTS(error=TTSError("down"))) as client:
        response = await client.post("/api/chat", json=PAYLOAD)

    body = response.json()
    assert response.status_code == 200
    assert body["reply"] == "Hola!"
    assert body["audio_b64"] is None
    assert body["tts_error"] == "down"


async def test_chat_maps_llm_failure_to_502() -> None:
    async with make_client(llm=FakeLLM(error=LLMError("LLM request failed with status 429"))) as c:
        response = await c.post("/api/chat", json=PAYLOAD)

    assert response.status_code == 502
    assert "429" in response.json()["detail"]


@pytest.mark.parametrize(
    "override",
    [{"length": "huge"}, {"message": ""}, {"session_id": ""}],
)
async def test_chat_rejects_invalid_payload(override: dict[str, str]) -> None:
    async with make_client() as client:
        response = await client.post("/api/chat", json={**PAYLOAD, **override})

    assert response.status_code == 422


async def test_index_page_is_served() -> None:
    async with make_client() as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>" in response.text
