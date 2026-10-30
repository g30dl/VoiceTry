from voice_chat.llm import Message


class FakeLLM:
    def __init__(self, reply: str = "Respuesta", error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.calls: list[list[Message]] = []

    async def complete(self, messages: list[Message]) -> str:
        self.calls.append([dict(m) for m in messages])
        if self.error:
            raise self.error
        return self.reply


class FakeTTS:
    def __init__(self, audio: bytes = b"audio", error: Exception | None = None) -> None:
        self.audio = audio
        self.error = error
        self.texts: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        self.texts.append(text)
        if self.error:
            raise self.error
        return self.audio
