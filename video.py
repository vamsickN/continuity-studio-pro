"""Video frame extraction for Continuity Studio Pro."""
import os
import subprocess
import json
from typing import List

import store


def extract_frames(
    video_path: str,
    fps: float = 1.0,
    max_frames: int = 40,
) -> List[str]:
    """Extract frames from a video at the specified FPS.
    
    Returns a list of URL paths to the extracted frame images.
    """
    output_dir = os.path.join(store.DATA_DIR, "frames")
    os.makedirs(output_dir, exist_ok=True)
    
    prefix = store.new_id("fr")
    pattern = os.path.join(output_dir, f"{prefix}_%04d.png")
    
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        "-frames:v", str(max_frames),
        "-q:v", "2",
        pattern,
        "-y", "-loglevel", "error",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    
    # Collect output files
    urls = []
    for i in range(1, max_frames + 1):
        fname = f"{prefix}_{i:04d}.png"
        path = os.path.join(output_dir, fname)
        if os.path.exists(path):
            urls.append(f"/data/frames/{fname}")
        else:
            break
    
    return urls


def probe_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0
    try:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0
