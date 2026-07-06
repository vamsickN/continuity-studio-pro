"""Image generation client for Continuity Studio Pro.

Supports OpenAI-compatible image generation endpoints (derouter, OpenRouter, etc.).
"""
import os
import base64
import time
from io import BytesIO
from typing import Optional

import requests

try:
    from PIL import Image
except ImportError:
    Image = None

import config


class ImageClient:
    """OpenAI-compatible image generation client."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key or config.API_KEY
        self.base_url = (base_url or config.BASE_URL).rstrip("/")
        self.model = model or config.MODEL
        self.timeout = config.TIMEOUT

    def ping(self) -> dict:
        """Check if the image endpoint is reachable."""
        if not self.api_key:
            return {"ok": False, "error": "No API key configured"}
        try:
            # Try a lightweight request to verify connectivity
            resp = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            return {"ok": resp.status_code in (200, 401, 403), "model": self.model}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def generate(
        self,
        prompt: str,
        size: str = "1536x1024",
        quality: str = "medium",
        n: int = 1,
    ):
        """Generate an image from a text prompt.
        
        Returns a PIL Image or raw bytes.
        """
        url = f"{self.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
            "response_format": "b64_json",
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        
        if resp.status_code == 429:
            # Rate limited - raise for retry logic
            raise RateLimitError("Rate limited by image provider")
        elif resp.status_code == 402:
            # Billing issue - try fallback if configured
            if config.IMAGE_FALLBACK_ON_402 and config.OPENROUTER_API_KEY:
                return self._fallback_generate(prompt, size, quality)
            raise BillingError("Insufficient balance")
        
        resp.raise_for_status()
        data = resp.json()
        
        # Parse response
        if "data" in data and len(data["data"]) > 0:
            item = data["data"][0]
            if "b64_json" in item:
                img_bytes = base64.b64decode(item["b64_json"])
                if Image:
                    return Image.open(BytesIO(img_bytes))
                return img_bytes
            elif "url" in item:
                img_resp = requests.get(item["url"], timeout=60)
                img_resp.raise_for_status()
                if Image:
                    return Image.open(BytesIO(img_resp.content))
                return img_resp.content
        
        raise RuntimeError("No image data in response")

    def _fallback_generate(self, prompt: str, size: str, quality: str):
        """Fallback to OpenRouter for image generation."""
        url = f"{config.OPENROUTER_BASE_URL}/images/generations"
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config.OPENROUTER_MODEL,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=config.OPENROUTER_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        if "data" in data and len(data["data"]) > 0:
            item = data["data"][0]
            if "b64_json" in item:
                img_bytes = base64.b64decode(item["b64_json"])
                if Image:
                    return Image.open(BytesIO(img_bytes))
                return img_bytes
        
        raise RuntimeError("Fallback generation returned no image")

    def edit(
        self,
        prompt: str,
        images: list,
        size: str = "1536x1024",
        quality: str = "medium",
    ):
        """Edit/transform images with a text prompt (image-to-image)."""
        url = f"{self.base_url}/images/edits"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        files = []
        for i, img in enumerate(images):
            if isinstance(img, bytes):
                files.append(("image", (f"ref_{i}.png", img, "image/png")))
            elif Image and hasattr(img, "save"):
                buf = BytesIO()
                img.save(buf, format="PNG")
                files.append(("image", (f"ref_{i}.png", buf.getvalue(), "image/png")))
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }
        
        resp = requests.post(url, headers=headers, data=data, files=files, timeout=self.timeout)
        resp.raise_for_status()
        result = resp.json()
        
        if "data" in result and len(result["data"]) > 0:
            item = result["data"][0]
            if "b64_json" in item:
                img_bytes = base64.b64decode(item["b64_json"])
                if Image:
                    return Image.open(BytesIO(img_bytes))
                return img_bytes
        
        raise RuntimeError("No image in edit response")


class RateLimitError(Exception):
    pass

class BillingError(Exception):
    pass
