import json

import httpx
import respx

from voice_chat.main import build_app

ENV = {
    "OPENROUTER_API_KEY": "k",
    "OPENROUTER_BASE_URL": "https://or.test/v1",
    "VOICESTUDIO_URL": "http://vs.test",
}


async def test_build_app_wires_model_and_voice_into_a_working_chat() -> None:
    with respx.mock(assert_all_called=True) as router:
        model = router.post("https://or.test/v1/chat/completions").respond(
            json={"choices": [{"message": {"role": "assistant", "content": "Hola"}}]}
        )
        voice = router.post("http://vs.test/v1/audio/speech").respond(content=b"RIFF")
        transport = httpx.ASGITransport(app=build_app(ENV))
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/chat", json={"session_id": "s1", "message": "Hola", "length": "short"}
            )

    assert response.status_code == 200
    assert response.json()["reply"] == "Hola"
    assert json.loads(model.calls.last.request.content)["model"] == "google/gemma-3-12b-it"
    assert json.loads(voice.calls.last.request.content)["voice"] == "chat-voice"
