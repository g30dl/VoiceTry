# Voice Chat

A small web chat where you type a question, Gemma answers in Spanish, and the
answer is spoken aloud in a fixed voice.

- **Model:** Gemma 3 12B (open weights), called through OpenRouter.
- **Voice:** [VoiceStudio](https://github.com/debpalash/VoiceStudio), running locally on your machine.

> **Status:** tested on Linux. Windows should work (the code has no OS-specific
> paths and the Windows-incompatible dependency is excluded automatically), but
> it has not been tried there.

## Quick path

1. Install [VoiceStudio](https://github.com/debpalash/VoiceStudio/releases/latest) and **keep it open**.
2. Install [uv](https://docs.astral.sh/uv/), the tool that installs this project's
   dependencies and manages Python. Do this once per computer, either with
   `pip install uv` (if you already have Python) or with the installer from
   [uv's documentation](https://docs.astral.sh/uv/getting-started/installation/)
   (no Python needed). Check it worked with `uv --version`.
3. Get an API key at [openrouter.ai](https://openrouter.ai).
4. Run these commands from the project folder:

   | Step | Linux / macOS | Windows (PowerShell) |
   |---|---|---|
   | Install the project's dependencies | `uv sync` | `uv sync` |
   | Add your key | `echo "OPENROUTER_API_KEY=your_key" > .env` | `Set-Content .env "OPENROUTER_API_KEY=your_key"` |
   | Create the voice | `uv run python -m voice_chat.setup_voice` | `uv run python -m voice_chat.setup_voice` |
   | Start the chat | `uv run uvicorn voice_chat.main:build_app --factory --port 8000` | same |

5. Open <http://127.0.0.1:8000>, leave the length on **Short**, and ask something.

Expected result: a "Thinking…" message, then the answer text and its voice
together. The voice starts playing by itself; the ↻ button replays it.

### If you just cloned this repository

Every step above is done **once, on your own computer**. You need nothing from
the author's machine: the voice profile is created inside *your* VoiceStudio by
the setup command, from a clip that ships with this repo. Check yourself:

- [ ] VoiceStudio is installed and open.
- [ ] `.env` holds your own OpenRouter key (never share or commit it).
- [ ] `uv run python -m voice_chat.setup_voice` printed `Created…` or `already exists`.
- [ ] <http://127.0.0.1:8000> opens the chat and the answer is spoken.

## Configuration

Set these in `.env` (never commit that file; it is already in `.gitignore`).

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENROUTER_API_KEY` | yes | none | Your OpenRouter key |
| `OPENROUTER_MODEL` | no | `google/gemma-3-12b-it` | Any OpenRouter chat model |
| `VOICESTUDIO_URL` | no | `http://127.0.0.1:3900` | Where VoiceStudio listens |
| `VOICESTUDIO_VOICE` | no | `chat-voice` | Voice profile name inside VoiceStudio |

## How it works

```
browser ──▶ POST /api/chat ──▶ Gemma (OpenRouter) ──▶ text
                          └──▶ VoiceStudio /v1/audio/speech ──▶ audio
```

- **The voice is a profile, not a setting.** Without a reference clip,
  VoiceStudio invents a different voice on every request. The setup command
  creates a profile named `chat-voice` from a bundled clip, so the voice stays
  the same. It lives inside *your* VoiceStudio, which is why every machine runs
  the setup command once. It is safe to run again.
- **Length selector.** Short, medium and long change the instruction sent to the
  model. Longer answers take longer to speak.
- **Memory.** The chat remembers the current page session only; reloading clears it.

## Things to know

| Topic | Detail |
|---|---|
| Speed | On the author's CPU-only laptop a short answer took about 20 to 50 seconds to speak. A supported GPU is likely faster, but that was not measured. |
| Cost | OpenRouter charges per token. At the time of writing, short questions cost a fraction of a cent. Check current prices. |
| Model changes | Free and older models disappear from OpenRouter. If the model stops working, change `OPENROUTER_MODEL`. |
| Quirks | Gemma occasionally starts a reply with a stray character, and may call itself Gemini. |

## Troubleshooting

| You see | Do this |
|---|---|
| `VoiceStudio is not reachable` | Open the VoiceStudio app and try again. |
| The voice changes between answers | Run `uv run python -m voice_chat.setup_voice`, then restart the chat. |
| `OPENROUTER_API_KEY is not set` | Create the `.env` file described above. |
| `LLM request failed with status 404` | The model was removed. Pick another in `OPENROUTER_MODEL`. |
| `LLM request failed with status 429` | You hit a rate limit. Wait a moment and retry. |
| `Error: ... Open VoiceStudio` when running setup | VoiceStudio must be running before the setup command. |

## Development

```bash
uv run pytest     # 40 tests, no network or VoiceStudio needed
```

The code is small on purpose: `chat.py` (conversation), `llm.py` (model client),
`tts.py` (voice client), `voice_profile.py` and `setup_voice.py` (voice setup),
`app.py` (web routes) and `static/index.html` (the page).

## Licenses and credits

- Gemma weights: open weights under Google's Gemma terms of use.
- [VoiceStudio](https://github.com/debpalash/VoiceStudio): AGPL-3.0. It runs as a separate program; this project only talks to it over HTTP.
- [OmniVoice](https://github.com/k2-fsa/OmniVoice), the default voice engine inside VoiceStudio: Apache-2.0.
- This project has no license yet. Add one before sharing it publicly.
