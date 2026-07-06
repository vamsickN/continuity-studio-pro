"""Video editing and assembly for Continuity Studio Pro."""
import os
import subprocess
import json
from typing import List, Optional

import store


def detect_scenes(video_path: str, threshold: float = 0.4) -> List[float]:
    """Detect scene changes in a video using ffmpeg's scene filter.
    
    Returns timestamps (seconds) of detected scene changes.
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-show_frames",
        "-of", "json",
        "-f", "lavfi",
        f"movie={video_path},select='gt(scene,{threshold})'",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        # Fallback: use simpler detection
        return _simple_scene_detect(video_path, threshold)
    
    try:
        data = json.loads(result.stdout)
        frames = data.get("frames", [])
        return [float(f.get("pts_time", 0)) for f in frames if "pts_time" in f]
    except (json.JSONDecodeError, KeyError):
        return []


def _simple_scene_detect(video_path: str, threshold: float) -> List[float]:
    """Fallback scene detection using select filter."""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-",
        "-loglevel", "info",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    times = []
    import re
    for match in re.finditer(r"pts_time:([\d.]+)", result.stderr):
        times.append(float(match.group(1)))
    return times


def probe_duration(video_path: str) -> float:
    """Get video duration."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0


def assemble_video(
    image_urls: List[str],
    audio_path: Optional[str] = None,
    fps: float = 0.5,
    duration_per_frame: float = 3.0,
    output_dir: str = "data",
) -> str:
    """Assemble images (and optionally audio) into a video.
    
    Returns the URL path to the assembled video.
    """
    os.makedirs(os.path.join(output_dir, "videos"), exist_ok=True)
    output_name = store.new_id("video") + ".mp4"
    output_path = os.path.join(output_dir, "videos", output_name)
    
    # Create a concat file for ffmpeg
    concat_file = os.path.join(output_dir, "_concat.txt")
    with open(concat_file, "w") as f:
        for url in image_urls:
            # Convert URL to local path
            if url.startswith("/data/"):
                path = os.path.join(output_dir, url.replace("/data/", "", 1))
            else:
                path = url
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path}'\n")
            f.write(f"duration {duration_per_frame}\n")
    
    cmd = [
        "ffmpeg",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-vf", f"fps={1/duration_per_frame},format=yuv420p,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
    ]
    
    if audio_path and os.path.exists(audio_path):
        cmd.extend(["-i", audio_path, "-c:a", "aac", "-shortest"])
    
    cmd.extend([output_path, "-y", "-loglevel", "error"])
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    # Cleanup
    try:
        os.remove(concat_file)
    except OSError:
        pass
    
    if result.returncode != 0:
        raise RuntimeError(f"Video assembly failed: {result.stderr}")
    
    return f"/data/videos/{output_name}"
