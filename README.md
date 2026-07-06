# Continuity Studio Pro

> AI-powered video & animation production studio. Generate characters, storyboards, voice-overs, and full video sequences using state-of-the-art AI models.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Character Sheet Generation** - Create consistent character reference sheets with AI
- **Storyboard & Shot Composition** - Generate frame-by-frame visual sequences
- **Multi-Provider AI** - Claude, Gemini, OpenAI, derouter, OpenRouter
- **Voice-Over** - ElevenLabs, Deepgram Aura, Piper (free local), MiMo
- **Video Assembly** - Scene detection, frame extraction, automated editing
- **YouTube Integration** - Direct upload with metadata
- **Professional Dark UI** - Sleek interface built for creators

## Quick Start

```bash
# Clone
git clone https://github.com/vamsickN/continuity-studio-pro.git
cd continuity-studio-pro

# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000 in your browser.

## Architecture

```
continuity-studio-pro/
├── app.py              # Main FastAPI application
├── config.py           # Centralized configuration
├── pipeline.py         # Image generation pipeline
├── claude_client.py    # Claude/Anthropic AI client
├── derouter.py         # Image generation router
├── voice.py            # TTS engine (multi-provider)
├── editor.py           # Video editing & assembly
├── video.py            # Frame extraction & processing
├── store.py            # State & asset management
├── static/
│   └── index.html      # Single-page application UI
└── data/               # Generated assets (gitignored)
```

## AI Providers

| Provider | Used For | Cost |
|----------|----------|------|
| derouter | Image generation | Pay-per-use |
| OpenRouter | Image fallback | Free tier available |
| Claude (Anthropic) | Scripts, vision, planning | Pay-per-use |
| Gemini | YouTube analysis | Free tier |
| ElevenLabs | Premium TTS | Pay-per-use |
| Deepgram Aura | Fast TTS | Pay-per-use |
| Piper | Local TTS | Free (runs locally) |

## Configuration

All settings are managed via environment variables. See `.env.example` for the full list.

Key settings:
- `DEROUTER_API_KEY` - Required for image generation
- `CLAUDE_API_KEY` - Required for scripts and planning
- `ELEVENLABS_API_KEY` - Optional, for premium voice-over
- `DEFAULT_SIZE` - Render resolution (default: 1536x1024)
- `DEFAULT_QUALITY` - Render quality: low/medium/high (default: medium)

## License

MIT
