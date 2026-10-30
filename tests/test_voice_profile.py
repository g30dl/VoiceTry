from pathlib import Path

import httpx
import pytest
import respx

from voice_chat.setup_voice import main
from voice_chat.voice_profile import (
    REFERENCE_AUDIO,
    REFERENCE_TEXT,
    VOICE_NAME,
    VoiceSetupError,
    ensure_voice_profile,
)

BASE_URL = "http://vs.test"


@pytest.fixture
def audio(tmp_path: Path) -> Path:
    path = tmp_path / "reference.wav"
    path.write_bytes(b"RIFF-fake-wav-bytes")
    return path


@respx.mock
async def test_creates_the_profile_when_it_does_not_exist(audio: Path) -> None:
    respx.get(f"{BASE_URL}/profiles").respond(json=[{"id": "a", "name": "other"}])
    create = respx.post(f"{BASE_URL}/profiles").respond(json={"id": "n", "name": "chat-voice"})

    async with httpx.AsyncClient() as http:
        created = await ensure_voice_profile(http, BASE_URL, "chat-voice", audio, "Hola mundo")

    assert created is True
    body = create.calls.last.request.content
    assert b'name="name"' in body and b"chat-voice" in body
    assert b'name="ref_text"' in body and b"Hola mundo" in body
    assert b'name="ref_audio"' in body and b"RIFF-fake-wav-bytes" in body


@pytest.mark.parametrize(
    "listing",
    [[{"name": "chat-voice"}], {"profiles": [{"name": "chat-voice"}]}],
)
@respx.mock
async def test_does_nothing_when_the_profile_already_exists(audio: Path, listing: object) -> None:
    respx.get(f"{BASE_URL}/profiles").respond(json=listing)
    create = respx.post(f"{BASE_URL}/profiles").respond(json={})

    async with httpx.AsyncClient() as http:
        created = await ensure_voice_profile(http, BASE_URL, "chat-voice", audio, "Hola")

    assert created is False
    assert not create.called


@respx.mock
async def test_unreachable_voicestudio_raises_a_clear_error(audio: Path) -> None:
    respx.get(f"{BASE_URL}/profiles").mock(side_effect=httpx.ConnectError("refused"))

    async with httpx.AsyncClient() as http:
        with pytest.raises(VoiceSetupError, match="VoiceStudio"):
            await ensure_voice_profile(http, BASE_URL, "chat-voice", audio, "Hola")


@respx.mock
async def test_a_failed_creation_includes_the_status(audio: Path) -> None:
    respx.get(f"{BASE_URL}/profiles").respond(json=[])
    respx.post(f"{BASE_URL}/profiles").respond(status_code=500)

    async with httpx.AsyncClient() as http:
        with pytest.raises(VoiceSetupError, match="500"):
            await ensure_voice_profile(http, BASE_URL, "chat-voice", audio, "Hola")


def test_the_bundled_reference_voice_ships_with_the_package() -> None:
    assert VOICE_NAME == "chat-voice"
    assert REFERENCE_TEXT.startswith("¡Hola!")
    assert REFERENCE_AUDIO.read_bytes()[:4] == b"RIFF"


@respx.mock
def test_cli_reports_creation(capsys: pytest.CaptureFixture[str]) -> None:
    respx.get(f"{BASE_URL}/profiles").respond(json=[])
    respx.post(f"{BASE_URL}/profiles").respond(json={"id": "n", "name": "chat-voice"})

    assert main({"VOICESTUDIO_URL": BASE_URL}) == 0
    assert "Created" in capsys.readouterr().out


@respx.mock
def test_cli_is_safe_to_run_twice(capsys: pytest.CaptureFixture[str]) -> None:
    respx.get(f"{BASE_URL}/profiles").respond(json=[{"name": "chat-voice"}])

    assert main({"VOICESTUDIO_URL": BASE_URL}) == 0
    assert "already exists" in capsys.readouterr().out


@respx.mock
def test_cli_tells_the_user_to_open_voicestudio(capsys: pytest.CaptureFixture[str]) -> None:
    respx.get(f"{BASE_URL}/profiles").mock(side_effect=httpx.ConnectError("refused"))

    assert main({"VOICESTUDIO_URL": BASE_URL}) == 1
    assert "Open VoiceStudio" in capsys.readouterr().err
