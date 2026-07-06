"""Image generation pipeline for Continuity Studio Pro.

Handles prompt construction, style injection, and character consistency.
"""
import re
from typing import List, Dict, Optional

try:
    from PIL import Image
except ImportError:
    Image = None

import config


def build_sheet_prompt(master_prompt: str, name: str, description: str) -> str:
    """Build a character sheet generation prompt."""
    parts = []
    if master_prompt:
        parts.append(f"MASTER STYLE: {master_prompt}")
    parts.append(
        f"Generate a detailed CHARACTER REFERENCE SHEET for '{name}'. "
        f"Show the character from multiple angles (front, side, 3/4 view, back). "
        f"Maintain consistent proportions, colors, and details across all views. "
        f"White/neutral background. Professional animation studio quality."
    )
    if description:
        parts.append(f"CHARACTER DETAILS: {description}")
    return "\n\n".join(parts)


def build_sequence_prompt(
    master_prompt: str,
    style_frames: List[Dict],
    characters: List[Dict],
    shot_description: str,
) -> str:
    """Build a shot generation prompt incorporating style and character references."""
    parts = []
    if master_prompt:
        parts.append(f"MASTER STYLE: {master_prompt}")
    if style_frames:
        parts.append(
            f"STYLE REFERENCE: Match the visual style, color palette, lighting, "
            f"and art direction shown in the {len(style_frames)} reference frames. "
            f"Copy the art style ONLY, not the specific content or people."
        )
    if characters:
        char_list = ", ".join(c["name"] for c in characters)
        parts.append(f"CHARACTERS IN SCENE: {char_list}")
    if shot_description:
        parts.append(f"SHOT: {shot_description}")
    return "\n\n".join(parts)


def parse_character_batch(text: str) -> List[Dict]:
    """Parse multi-character input text.
    
    Expected format (separated by blank lines):
        Character Name
        Description text here
        
        Another Character
        Their description
    """
    entries = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        name = lines[0].strip()
        description = "\n".join(lines[1:]).strip()
        if name:
            entries.append({"name": name, "description": description})
    return entries


def downsize_for_vision(img, max_dim: int = 1024):
    """Resize image to fit within max_dim for vision API calls."""
    if Image is None:
        return img
    if not hasattr(img, "size"):
        return img
    w, h = img.size
    if w <= max_dim and h <= max_dim:
        return img
    ratio = min(max_dim / w, max_dim / h)
    new_size = (int(w * ratio), int(h * ratio))
    return img.resize(new_size, Image.LANCZOS)
