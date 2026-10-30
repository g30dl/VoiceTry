import time
from dataclasses import dataclass
from typing import Literal, Protocol

from voice_chat.llm import LLMError, Message
from voice_chat.tts import TTSError

Length = Literal["short", "medium", "long"]

MAX_HISTORY_MESSAGES = 20

# Gemma does not reliably support the system role, so the instruction travels
# inside the current user turn. The stored history keeps the raw message.
LENGTH_INSTRUCTIONS: dict[str, str] = {
    "short": "Reply in Spanish with one or two short sentences. Plain text only, no markdown.",
    "medium": "Reply in Spanish with one short paragraph of three to five sentences. "
    "Plain text only, no markdown.",
    "long": "Reply in Spanish with two or three well developed paragraphs. "
    "Plain text only, no markdown.",
}


class LLM(Protocol):
    async def complete(self, messages: list[Message]) -> str: ...


class TTS(Protocol):
    async def synthesize(self, text: str) -> bytes: ...


@dataclass(frozen=True)
class ChatReply:
    text: str
    audio: bytes | None
    tts_error: str | None
    llm_ms: int
    tts_ms: int | None


def _elapsed_ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)


class ChatService:
    def __init__(self, llm: LLM, tts: TTS) -> None:
        self._llm = llm
        self._tts = tts
        self._sessions: dict[str, list[Message]] = {}

    async def reply(self, session_id: str, message: str, length: Length) -> ChatReply:
        history = self._sessions.setdefault(session_id, [])
        turn = {"role": "user", "content": f"[{LENGTH_INSTRUCTIONS[length]}]\n\n{message}"}
        messages = [*history[-MAX_HISTORY_MESSAGES:], turn]
        while messages[0]["role"] != "user":
            messages.pop(0)

        start = time.perf_counter()
        text = (await self._llm.complete(messages)).strip()
        llm_ms = _elapsed_ms(start)
        if not text:
            raise LLMError("The model returned an empty answer")

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": text})

        start = time.perf_counter()
        try:
            audio = await self._tts.synthesize(text)
        except TTSError as e:
            return ChatReply(text, None, str(e), llm_ms, None)
        return ChatReply(text, audio, None, llm_ms, _elapsed_ms(start))
