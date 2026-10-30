import httpx


class TTSError(Exception):
    pass


class TTSClient:
    """Client for an OpenAI-compatible speech endpoint (VoiceStudio's local backend)."""

    def __init__(self, base_url: str, http: httpx.AsyncClient, voice: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._http = http
        self._voice = voice
        self._model = model

    async def synthesize(self, text: str) -> bytes:
        try:
            response = await self._http.post(
                f"{self._base_url}/v1/audio/speech",
                json={
                    "model": self._model,
                    "input": text,
                    "voice": self._voice,
                    "response_format": "wav",
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise TTSError(f"VoiceStudio failed with status {e.response.status_code}") from e
        except httpx.ConnectError as e:
            raise TTSError("VoiceStudio is not reachable. Is the app open?") from e
        except httpx.HTTPError as e:
            raise TTSError(f"VoiceStudio request failed: {e!r}") from e
        return response.content
