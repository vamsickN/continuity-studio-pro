"""Claude/Anthropic AI client for Continuity Studio Pro.

Handles:
- Script generation
- Scene analysis (vision)
- Prompt enhancement
- Edit planning
"""
import base64
import json
from io import BytesIO
from typing import Optional, List, Dict

import requests

try:
    from PIL import Image
except ImportError:
    Image = None

import config


class ClaudeClient:
    """Anthropic-compatible Claude API client."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key or config.CLAUDE_API_KEY
        self.base_url = (base_url or config.CLAUDE_BASE_URL).rstrip("/")
        self.model = model or config.CLAUDE_MODEL

    def ping(self) -> dict:
        """Check connectivity."""
        if not self.api_key:
            return {"ok": False, "error": "No Claude API key configured"}
        try:
            # Simple connectivity check
            resp = requests.post(
                f"{self.base_url}/v1/messages",
                headers=self._headers(),
                json={
                    "model": self.model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "hi"}],
                },
                timeout=15,
            )
            # 200 = works, 401/403 = auth issue but reachable
            return {"ok": resp.status_code == 200, "model": self.model}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _chat(self, system: str, messages: list, max_tokens: int = 4096) -> str:
        """Send a chat completion request."""
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        resp = requests.post(
            f"{self.base_url}/v1/messages",
            headers=self._headers(),
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        # Extract text from response
        content = data.get("content", [])
        texts = [block["text"] for block in content if block.get("type") == "text"]
        return "\n".join(texts)

    def analyse_scene(self, img, question: str = "") -> str:
        """Analyse an image using Claude's vision capabilities."""
        img_b64 = self._encode_image(img)
        system = (
            "You are a visual analysis expert for animation/video production. "
            "Describe what you see in detail: characters, setting, lighting, mood, "
            "color palette, composition, and any notable elements."
        )
        content = []
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64,
            },
        })
        content.append({
            "type": "text",
            "text": question or "Describe this scene in detail for animation production.",
        })
        return self._chat(system, [{"role": "user", "content": content}])

    def generate_script(self, description: str) -> List[Dict]:
        """Generate a production script from a description."""
        system = (
            "You are a professional script writer for animated video production. "
            "Break the user's input into numbered scenes. For each scene provide:\n"
            "- number (int)\n"
            "- heading (short title)\n"
            "- action (what happens visually)\n"
            "- voice_over (narration text)\n"
            "- prompt (detailed image generation prompt)\n\n"
            "Return ONLY valid JSON: an array of scene objects. No markdown, no explanation."
        )
        messages = [{"role": "user", "content": description}]
        result = self._chat(system, messages)
        # Parse JSON from response
        try:
            # Strip any markdown code fences
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON array in response
            import re
            match = re.search(r"\[.*\]", result, re.DOTALL)
            if match:
                return json.loads(match.group())
            # Return as single scene
            return [{
                "number": 1,
                "heading": "Scene 1",
                "action": result,
                "voice_over": "",
                "prompt": "",
            }]

    def enhance_prompt(self, base_prompt: str, style_notes: str = "") -> str:
        """Enhance a basic prompt into a detailed image generation prompt."""
        system = (
            "You are an expert at writing image generation prompts. "
            "Take the user's basic description and expand it into a detailed, "
            "specific prompt optimized for AI image generation. Include: composition, "
            "lighting, color palette, camera angle, mood, and style details. "
            "Return ONLY the enhanced prompt text, nothing else."
        )
        user_msg = base_prompt
        if style_notes:
            user_msg += f"\n\nStyle guidance: {style_notes}"
        return self._chat(system, [{"role": "user", "content": user_msg}], max_tokens=1024)

    def _encode_image(self, img) -> str:
        """Encode an image to base64."""
        if isinstance(img, str):
            # Already base64
            return img
        if isinstance(img, bytes):
            return base64.b64encode(img).decode()
        if Image and hasattr(img, "save"):
            buf = BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()
        raise ValueError("Cannot encode image")
