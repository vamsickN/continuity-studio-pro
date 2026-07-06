"""State & asset management for Continuity Studio Pro.

Handles:
- Project state persistence (JSON)
- Image/asset writing
- Unique ID generation
"""
import os
import json
import uuid
import time
from datetime import datetime, timezone
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    Image = None

import config

DATA_DIR = config.DATA_DIR
STATE_FILE = os.path.join(DATA_DIR, "state.json")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")


def init():
    """Create data directories on startup."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "characters"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "images"), exist_ok=True)
    if not os.path.exists(STATE_FILE):
        save_state(default_state())


def default_state():
    return {
        "master_prompt": "",
        "style_frames": [],
        "characters": [],
        "generated_images": [],
        "scenes": [],
    }


def load_state():
    """Load project state from disk."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_state()


def save_state(st):
    """Persist project state to disk."""
    with open(STATE_FILE, "w") as f:
        json.dump(st, f, indent=2)


def new_id(prefix=""):
    """Generate a unique ID."""
    short = uuid.uuid4().hex[:12]
    return f"{prefix}_{short}" if prefix else short


def now():
    """ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def write_image(subdir, img):
    """Write a PIL Image to disk, return its relative URL path."""
    if Image is None:
        raise RuntimeError("Pillow is required for image operations")
    name = new_id("img") + ".png"
    path = os.path.join(DATA_DIR, subdir, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(img, bytes):
        with open(path, "wb") as f:
            f.write(img)
    elif hasattr(img, "save"):
        img.save(path)
    else:
        with open(path, "wb") as f:
            f.write(img)
    return f"/data/{subdir}/{name}"


def write_bytes(subdir, data, ext=".png"):
    """Write raw bytes to disk, return relative URL path."""
    name = new_id("file") + ext
    path = os.path.join(DATA_DIR, subdir, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return f"/data/{subdir}/{name}"


def read_image(url_or_path):
    """Read an image from a local path or URL."""
    if Image is None:
        raise RuntimeError("Pillow is required")
    if url_or_path.startswith("/data/"):
        # Local file
        path = os.path.join(DATA_DIR, url_or_path.replace("/data/", "", 1))
        return Image.open(path)
    elif url_or_path.startswith(("http://", "https://")):
        import requests
        resp = requests.get(url_or_path, timeout=30)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content))
    else:
        return Image.open(url_or_path)
