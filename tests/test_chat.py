import pytest

from tests.fakes import FakeLLM, FakeTTS
from voice_chat.chat import LENGTH_INSTRUCTIONS, MAX_HISTORY_MESSAGES, ChatService
from voice_chat.llm import LLMError
from voice_chat.tts import TTSError


def make_service(llm: FakeLLM | None = None, tts: FakeTTS | None = None) -> ChatService:
    return ChatService(llm=llm or FakeLLM(), tts=tts or FakeTTS())


async def test_reply_contains_text_audio_and_timings() -> None:
    tts = FakeTTS(audio=b"wav-bytes")
    service = make_service(FakeLLM(reply="Hola, soy Gemma."), tts)

    result = await service.reply("s1", "Hola", "short")

    assert result.text == "Hola, soy Gemma."
    assert result.audio == b"wav-bytes"
    assert result.tts_error is None
    assert result.llm_ms >= 0
    assert result.tts_ms is not None and result.tts_ms >= 0
    assert tts.texts == ["Hola, soy Gemma."]


async def test_reply_text_is_stripped_before_speaking_and_storing() -> None:
    tts = FakeTTS()
    llm = FakeLLM(reply="\nDos más dos es cuatro.\n")
    service = make_service(llm, tts)

    result = await service.reply("s1", "Cuanto es 2+2?", "short")
    await service.reply("s1", "Y 3+3?", "short")

    assert result.text == "Dos más dos es cuatro."
    assert tts.texts[0] == "Dos más dos es cuatro."
    assert llm.calls[1][1]["content"] == "Dos más dos es cuatro."


async def test_current_turn_carries_the_length_instruction() -> None:
    llm = FakeLLM()
    service = make_service(llm)

    await service.reply("s1", "Qué es Python?", "short")

    last = llm.calls[0][-1]
    assert last["role"] == "user"
    assert LENGTH_INSTRUCTIONS["short"] in last["content"]
    assert "Qué es Python?" in last["content"]
    assert all(m["role"] != "system" for m in llm.calls[0])


async def test_history_is_remembered_within_a_session() -> None:
    llm = FakeLLM(reply="Primera")
    service = make_service(llm)
    await service.reply("s1", "Pregunta uno", "short")

    llm.reply = "Segunda"
    await service.reply("s1", "Pregunta dos", "short")

    second_call = llm.calls[1]
    assert [m["role"] for m in second_call] == ["user", "assistant", "user"]
    assert second_call[0]["content"] == "Pregunta uno"
    assert second_call[1]["content"] == "Primera"
    assert "Pregunta dos" in second_call[2]["content"]


async def test_length_can_change_between_turns_without_leaking_old_instruction() -> None:
    llm = FakeLLM()
    service = make_service(llm)
    await service.reply("s1", "Uno", "short")

    await service.reply("s1", "Dos", "long")

    last = llm.calls[1][-1]["content"]
    assert LENGTH_INSTRUCTIONS["long"] in last
    assert LENGTH_INSTRUCTIONS["short"] not in last
    assert LENGTH_INSTRUCTIONS["short"] not in llm.calls[1][0]["content"]


async def test_sessions_are_isolated() -> None:
    llm = FakeLLM()
    service = make_service(llm)
    await service.reply("s1", "Soy A", "short")

    await service.reply("s2", "Soy B", "short")

    assert len(llm.calls[1]) == 1


async def test_history_sent_to_the_model_is_capped() -> None:
    llm = FakeLLM()
    service = make_service(llm)

    for i in range(30):
        await service.reply("s1", f"Pregunta {i}", "short")

    last_call = llm.calls[-1]
    assert len(last_call) <= MAX_HISTORY_MESSAGES + 1
    assert "Pregunta 29" in last_call[-1]["content"]
    assert last_call[0]["role"] == "user"


async def test_tts_failure_still_returns_the_text() -> None:
    service = make_service(tts=FakeTTS(error=TTSError("VoiceStudio is not reachable")))

    result = await service.reply("s1", "Hola", "short")

    assert result.text == "Respuesta"
    assert result.audio is None
    assert result.tts_error == "VoiceStudio is not reachable"
    assert result.tts_ms is None


async def test_llm_failure_propagates_and_leaves_history_untouched() -> None:
    llm = FakeLLM(error=LLMError("boom"))
    service = make_service(llm)

    with pytest.raises(LLMError):
        await service.reply("s1", "Se pierde", "short")

    llm.error = None
    await service.reply("s1", "Ahora si", "short")
    assert len(llm.calls[1]) == 1


async def test_an_empty_model_answer_is_an_error() -> None:
    service = make_service(FakeLLM(reply="  "))

    with pytest.raises(LLMError, match="empty"):
        await service.reply("s1", "Hola", "short")
