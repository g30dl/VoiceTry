import json

import httpx
import pytest
import respx

from voice_chat.llm import LLMClient, LLMError

BASE_URL = "https://openrouter.test/api/v1"
MODEL = "google/gemma-3-12b-it"


@pytest.fixture
def llm() -> LLMClient:
    return LLMClient(
        base_url=BASE_URL, api_key="secret-key", model=MODEL, http=httpx.AsyncClient()
    )


@respx.mock
async def test_complete_returns_assistant_text(llm: LLMClient) -> None:
    route = respx.post(f"{BASE_URL}/chat/completions").respond(
        json={"choices": [{"message": {"role": "assistant", "content": "Hola!"}}]}
    )
    messages = [{"role": "user", "content": "Hola"}]

    reply = await llm.complete(messages)

    assert reply == "Hola!"
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer secret-key"
    assert json.loads(request.content) == {"model": MODEL, "messages": messages}


@respx.mock
async def test_complete_raises_llm_error_on_http_error(llm: LLMClient) -> None:
    respx.post(f"{BASE_URL}/chat/completions").respond(status_code=429, text="slow down")

    with pytest.raises(LLMError, match="429"):
        await llm.complete([{"role": "user", "content": "Hola"}])


@pytest.mark.parametrize(
    "payload",
    [{"choices": []}, {"choices": [{"message": {"role": "assistant", "content": None}}]}],
)
@respx.mock
async def test_complete_raises_llm_error_on_unexpected_payload(
    llm: LLMClient, payload: dict
) -> None:
    respx.post(f"{BASE_URL}/chat/completions").respond(json=payload)

    with pytest.raises(LLMError):
        await llm.complete([{"role": "user", "content": "Hola"}])
