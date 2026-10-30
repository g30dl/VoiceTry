import json

import httpx
import pytest
import respx

from voice_chat.tts import TTSClient, TTSError

BASE_URL = "http://voicestudio.test"


@pytest.fixture
def tts() -> TTSClient:
    return TTSClient(base_url=BASE_URL, http=httpx.AsyncClient(), voice="alloy", model="tts-1")


@respx.mock
async def test_synthesize_returns_wav_bytes(tts: TTSClient) -> None:
    route = respx.post(f"{BASE_URL}/v1/audio/speech").respond(
        content=b"RIFFfakewav", headers={"content-type": "audio/wav"}
    )

    audio = await tts.synthesize("Hola")

    assert audio == b"RIFFfakewav"
    assert json.loads(route.calls.last.request.content) == {
        "model": "tts-1",
        "input": "Hola",
        "voice": "alloy",
        "response_format": "wav",
    }


@respx.mock
async def test_synthesize_raises_tts_error_on_http_error(tts: TTSClient) -> None:
    respx.post(f"{BASE_URL}/v1/audio/speech").respond(status_code=500)

    with pytest.raises(TTSError, match="500"):
        await tts.synthesize("Hola")


@respx.mock
async def test_synthesize_raises_tts_error_when_unreachable(tts: TTSClient) -> None:
    respx.post(f"{BASE_URL}/v1/audio/speech").mock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(TTSError, match="VoiceStudio"):
        await tts.synthesize("Hola")
