"""Central configuration for Continuity Studio Pro.
All values can be overridden via environment variables or .env file."""
import os

def _get(name, default=None):
    v = os.environ.get(name)
    return v if v not in (None, "") else default

def _int(name, default):
    try:
        return int(float(_get(name, str(default))))
    except (TypeError, ValueError):
        return default

# --- Image Generation (derouter / OpenAI-compatible) ---
API_KEY = _get("DEROUTER_API_KEY", "")
BASE_URL = _get("DEROUTER_BASE_URL", "https://api-direct.derouter.network/openai/v1")
MODEL = _get("IMAGE_MODEL", "gpt-image-2")
TIMEOUT = int(_get("REQUEST_TIMEOUT", "600"))

# --- Claude / Anthropic ---
CLAUDE_API_KEY = _get("CLAUDE_API_KEY", _get("ANTHROPIC_API_KEY", ""))
CLAUDE_BASE_URL = _get("CLAUDE_BASE_URL", "https://api.derouter.network/proxy")
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-sonnet-4-6")
CLAUDE_MODELS = [
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
]

# --- ElevenLabs TTS ---
ELEVENLABS_API_KEY = _get("ELEVENLABS_API_KEY", "")
ELEVENLABS_BASE_URL = _get("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")
ELEVENLABS_VOICE_ID = _get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL = _get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# --- Deepgram Aura TTS ---
DEEPGRAM_API_KEY = _get("DEEPGRAM_API_KEY", "")
DEEPGRAM_BASE_URL = _get("DEEPGRAM_BASE_URL", "https://api.deepgram.com/v1")
DEEPGRAM_MODEL = _get("DEEPGRAM_MODEL", "aura-2-thalia-en")
DEEPGRAM_VOICE_ID = _get("DEEPGRAM_VOICE_ID", "aura-2-thalia-en")
DEEPGRAM_ENCODING = _get("DEEPGRAM_ENCODING", "wav")

# --- Piper TTS (local, free) ---
PIPER_VOICE = _get("PIPER_VOICE", "amy")
PIPER_USE_GPU = _get("PIPER_USE_GPU", "false").lower() in ("1", "true", "yes")
PIPER_LENGTH_SCALE = float(_get("PIPER_LENGTH_SCALE", "1.0"))
PIPER_NOISE_SCALE = float(_get("PIPER_NOISE_SCALE", "0.667"))
PIPER_NOISE_W_SCALE = float(_get("PIPER_NOISE_W_SCALE", "0.8"))
PIPER_MODELS_DIR = _get("PIPER_MODELS_DIR", "")
PIPER_USE_WHISPER_FOR_TIMING = _get("PIPER_USE_WHISPER_FOR_TIMING", "true").lower() in (
    "1", "true", "yes",
)

# --- MiMo TTS ---
MIMO_API_KEY = _get("MIMO_API_KEY", "")
MIMO_BASE_URL = _get("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
MIMO_MODEL = _get("MIMO_MODEL", "mimo-v2.5-tts")
MIMO_VOICE_ID = _get("MIMO_VOICE_ID", "Chloe")
MIMO_STYLE = _get("MIMO_STYLE", "Clear, natural, engaging narration voice.")

# --- Google OAuth ---
GOOGLE_CLIENT_ID = _get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = _get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = _get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# --- OpenRouter (fallback) ---
OPENROUTER_API_KEY = _get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = _get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = _get("OPENROUTER_MODEL", "sourceful/riverflow-v2.5-pro:free")
OPENROUTER_TIMEOUT = int(_get("OPENROUTER_TIMEOUT", "600"))
OPENROUTER_MODELS = [
    "sourceful/riverflow-v2.5-fast:free",
    "sourceful/riverflow-v2.5-pro:free",
]

# --- Gemini ---
GEMINI_API_KEY = _get("GEMINI_API_KEY", "")
GEMINI_BASE_URL = _get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-flash-latest",
    "gemini-pro-latest",
]

# --- 9Router ---
NINEROUTER_API_KEY = _get("NINEROUTER_API_KEY", "")
NINEROUTER_BASE_URL = _get("NINEROUTER_BASE_URL", "http://127.0.0.1:20128")
NINEROUTER_MODEL = _get("NINEROUTER_MODEL", "cc/claude-sonnet-4-6")
NINEROUTER_IMAGE_BASE_URL = _get("NINEROUTER_IMAGE_BASE_URL", "http://127.0.0.1:20128/v1")
NINEROUTER_IMAGE_MODEL = _get("NINEROUTER_IMAGE_MODEL", "gpt-image-2")
CLAUDE_FALLBACK_MODEL = _get("CLAUDE_FALLBACK_MODEL", "")
NINEROUTER_MODELS = [
    "cc/claude-sonnet-4-6",
    "cc/claude-opus-4-8",
    "cc/claude-opus-4-7",
    "cc/claude-haiku-4-5-20251001",
    "cx/gpt-5.5",
    "kr/claude-sonnet-4.5",
]

# --- AgentRouter ---
AGENTROUTER_API_KEY = _get("AGENTROUTER_API_KEY", "")
AGENTROUTER_BASE_URL = _get("AGENTROUTER_BASE_URL", "https://agentrouter.org")
AGENTROUTER_MODEL = _get("AGENTROUTER_MODEL", "claude-sonnet-4-6")
AGENTROUTER_MODELS = [
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
]

# --- Render Defaults ---
DEFAULT_SIZE = _get("DEFAULT_SIZE", "1536x1024")
DEFAULT_QUALITY = _get("DEFAULT_QUALITY", "medium")
MULTI_IMAGE_EDIT = _get("MULTI_IMAGE_EDIT", "false").lower() == "true"
SUPPORTED_SIZES = [
    "1920x1080", "1024x1024", "1024x1536", "1536x1024", "2048x2048", "3840x2160", "auto",
]
SUPPORTED_QUALITIES = ["low", "medium", "high", "auto"]

# --- Image Queue / Rate Limiting ---
IMAGE_MAX_CONCURRENCY = max(1, _int("IMAGE_MAX_CONCURRENCY", 2))
IMAGE_REQUEST_DELAY_MS = max(0, _int("IMAGE_REQUEST_DELAY_MS", 50))
IMAGE_MAX_RETRIES = max(0, _int("IMAGE_MAX_RETRIES", 6))
IMAGE_BACKOFF_BASE_MS = max(100, _int("IMAGE_BACKOFF_BASE_MS", 1500))
IMAGE_BACKOFF_MAX_MS = max(1000, _int("IMAGE_BACKOFF_MAX_MS", 30000))
IMAGE_RATE_LIMIT_COOLDOWN_MS = max(1000, _int("IMAGE_RATE_LIMIT_COOLDOWN_MS", 18000))
IMAGE_FALLBACK_ON_402 = _get("IMAGE_FALLBACK_ON_402", "true").lower() in ("1", "true", "yes")

# --- Style Ref Settings ---
FRAME_FPS = float(_get("FRAME_FPS", "1"))
DATA_DIR = _get("DATA_DIR", "data")
STYLE_REF_COUNT = int(_get("STYLE_REF_COUNT", "6"))
STYLE_FRAMES_WITH_CHARS = int(_get("STYLE_FRAMES_WITH_CHARS", "4"))
STYLE_FRAMES_NO_CHARS = int(_get("STYLE_FRAMES_NO_CHARS", "6"))
MAX_REF_IMAGES = int(_get("MAX_REF_IMAGES", "10"))

# --- Auth ---
AUTH_REQUIRED = _get("AUTH_REQUIRED", "false").lower() in ("1", "true", "yes")
SESSION_SECRET = _get("SESSION_SECRET", "continuity-studio-default-session-key")

# --- OpenAI Direct ---
OPENAI_API_KEY = _get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = _get("OPENAI_BASE_URL", "https://api.openai.com/v1")

# --- Anthropic Direct ---
ANTHROPIC_DIRECT_API_KEY = _get("ANTHROPIC_DIRECT_API_KEY", "")
ANTHROPIC_DIRECT_BASE_URL = "https://api.anthropic.com"
