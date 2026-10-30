from pathlib import Path
from typing import Any

import httpx

VOICE_NAME = "chat-voice"
# The delivery of the reference clip is what the cloned voice imitates, so this
# sentence is an expressive greeting on purpose. It must match the audio.
REFERENCE_TEXT = "¡Hola! ¿Cómo estás? ¡Qué alegría saludarte, estoy aquí para ayudarte!"
REFERENCE_AUDIO = Path(__file__).parent / "assets" / "chat-voice.wav"


class VoiceSetupError(Exception):
    pass


def _names(listing: Any) -> set[str]:
    profiles = listing.get("profiles", []) if isinstance(listing, dict) else listing
    return {p["name"] for p in profiles if isinstance(p, dict) and "name" in p}


async def ensure_voice_profile(
    http: httpx.AsyncClient,
    base_url: str,
    name: str = VOICE_NAME,
    audio: Path = REFERENCE_AUDIO,
    reference_text: str = REFERENCE_TEXT,
) -> bool:
    """Create the VoiceStudio voice profile unless it already exists.

    Returns True when it was created, False when it was already there.
    """
    base_url = base_url.rstrip("/")
    try:
        listing = await http.get(f"{base_url}/profiles")
        listing.raise_for_status()
        if name in _names(listing.json()):
            return False
        created = await http.post(
            f"{base_url}/profiles",
            data={"name": name, "ref_text": reference_text},
            files={"ref_audio": (audio.name, audio.read_bytes(), "audio/wav")},
        )
        created.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise VoiceSetupError(f"VoiceStudio failed with status {e.response.status_code}") from e
    except httpx.ConnectError as e:
        raise VoiceSetupError(f"VoiceStudio is not reachable at {base_url}") from e
    except (httpx.HTTPError, ValueError) as e:
        raise VoiceSetupError(f"VoiceStudio request failed: {e!r}") from e
    return True
