import httpx

Message = dict[str, str]


class LLMError(Exception):
    pass


class LLMClient:
    """Client for any OpenAI-compatible chat completions API (e.g. OpenRouter)."""

    def __init__(
        self, base_url: str, api_key: str, model: str, http: httpx.AsyncClient
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._http = http

    async def complete(self, messages: list[Message]) -> str:
        try:
            response = await self._http.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "messages": messages},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise LLMError(f"LLM request failed with status {e.response.status_code}") from e
        except httpx.HTTPError as e:
            raise LLMError(f"LLM request failed: {e!r}") from e

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise LLMError("LLM returned an unexpected response") from e
        if not isinstance(content, str):
            raise LLMError("LLM returned an unexpected response")
        return content
