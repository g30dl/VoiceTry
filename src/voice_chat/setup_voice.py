"""Create the `chat-voice` profile in VoiceStudio. Safe to run more than once.

Usage: uv run python -m voice_chat.setup_voice
"""

import asyncio
import os
import sys
from collections.abc import Mapping

import httpx
from dotenv import load_dotenv

from voice_chat.voice_profile import VOICE_NAME, VoiceSetupError, ensure_voice_profile


async def _run(base_url: str) -> bool:
    async with httpx.AsyncClient(timeout=120) as http:
        return await ensure_voice_profile(http, base_url)


def main(env: Mapping[str, str] | None = None) -> int:
    if env is None:
        load_dotenv()
        env = os.environ
    base_url = env.get("VOICESTUDIO_URL", "http://127.0.0.1:3900")
    try:
        created = asyncio.run(_run(base_url))
    except VoiceSetupError as e:
        print(f"Error: {e}. Open VoiceStudio and try again.", file=sys.stderr)
        return 1
    print(
        f"Created the '{VOICE_NAME}' voice profile."
        if created
        else f"The '{VOICE_NAME}' voice profile already exists. Nothing to do."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
