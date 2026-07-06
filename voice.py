"""Voice/TTS client for Continuity Studio Pro.

Supports multiple TTS providers:
- ElevenLabs (premium)
- Deepgram Aura (fast)
- Piper (local/free)
- MiMo (alternative)
"""
import os
import json
from typing import Optional

import requests

import config
import store


class VoiceClient:
    """Multi-provider TTS client."""

    def __init__(self, api_key: str = "", model: str = "", voice_id: str = ""):
        self.api_key = api_key or config.ELEVENLABS_API_KEY
        self.model = model or config.ELEVENLABS_MODEL
        self.voice_id = voice_id or config.ELEVENLABS_VOICE_ID

    def ping(self) -> dict:
        """Check if ElevenLabs is configured."""
        if not self.api_key:
            return {"ok": False, "error": "No ElevenLabs API key"}
        try:
            resp = requests.get(
                f"{config.ELEVENLABS_BASE_URL}/voices",
                headers={"xi-api-key": self.api_key},
                timeout=10,
            )
            return {"ok": resp.status_code == 200}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def synthesize(self, text: str, provider: str = "elevenlabs") -> str:
        """Synthesize text to speech. Returns URL path to audio file."""
        if provider == "piper":
            return self._synth_piper(text)
        elif provider == "deepgram":
            return self._synth_deepgram(text)
        elif provider == "mimo":
            return self._synth_mimo(text)
        else:
            return self._synth_elevenlabs(text)

    def _synth_elevenlabs(self, text: str) -> str:
        """ElevenLabs TTS."""
        url = f"{config.ELEVENLABS_BASE_URL}/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return self._save_audio(resp.content, "mp3")

    def _synth_deepgram(self, text: str) -> str:
        """Deepgram Aura TTS."""
        url = f"{config.DEEPGRAM_BASE_URL}/speak"
        headers = {
            "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
            "Content-Type": "application/json",
        }
        params = {"model": config.DEEPGRAM_MODEL, "encoding": config.DEEPGRAM_ENCODING}
        payload = {"text": text}
        resp = requests.post(url, json=payload, headers=headers, params=params, timeout=60)
        resp.raise_for_status()
        ext = "wav" if config.DEEPGRAM_ENCODING == "wav" else "mp3"
        return self._save_audio(resp.content, ext)

    def _synth_piper(self, text: str) -> str:
        """Piper local TTS (requires piper-tts package)."""
        try:
            from piper import PiperVoice
        except ImportError:
            raise RuntimeError("piper-tts not installed. Run: pip install piper-tts")
        
        models_dir = config.PIPER_MODELS_DIR or os.path.join(store.DATA_DIR, "piper_models")
        os.makedirs(models_dir, exist_ok=True)
        
        voice = PiperVoice.load(
            config.PIPER_VOICE,
            download_dir=models_dir,
            use_cuda=config.PIPER_USE_GPU,
        )
        
        import wave
        import io
        
        audio_buf = io.BytesIO()
        with wave.open(audio_buf, "wb") as wf:
            voice.synthesize(
                text,
                wf,
                length_scale=config.PIPER_LENGTH_SCALE,
                noise_scale=config.PIPER_NOISE_SCALE,
                noise_w=config.PIPER_NOISE_W_SCALE,
            )
        
        return self._save_audio(audio_buf.getvalue(), "wav")

    def _synth_mimo(self, text: str) -> str:
        """Xiaomi MiMo TTS."""
        url = f"{config.MIMO_BASE_URL}/audio/speech"
        headers = {
            "Authorization": f"Bearer {config.MIMO_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config.MIMO_MODEL,
            "input": text,
            "voice": config.MIMO_VOICE_ID,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return self._save_audio(resp.content, "wav")

    def _save_audio(self, data: bytes, ext: str) -> str:
        """Save audio bytes to disk, return URL path."""
        audio_dir = os.path.join(store.DATA_DIR, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        name = store.new_id("audio") + f".{ext}"
        path = os.path.join(audio_dir, name)
        with open(path, "wb") as f:
            f.write(data)
        return f"/data/audio/{name}"

    def list_voices(self) -> list:
        """List available ElevenLabs voices."""
        if not self.api_key:
            return []
        try:
            resp = requests.get(
                f"{config.ELEVENLABS_BASE_URL}/voices",
                headers={"xi-api-key": self.api_key},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"id": v["voice_id"], "name": v["name"], "category": v.get("category", "")}
                for v in data.get("voices", [])
            ]
        except Exception:
            return []
