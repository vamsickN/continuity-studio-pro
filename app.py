"""Continuity Studio Pro - Main FastAPI Application.

Clean entry point that mounts all API routes. Run with:
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
"""
import os
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import store

# Initialize store on startup
store.init()

app = FastAPI(
    title="Continuity Studio Pro",
    description="AI-powered video & animation production studio",
    version="2.0.0",
)

# --- Lazy imports for heavy modules (faster cold start) ---
def _get_pipeline():
    import pipeline
    return pipeline

def _get_editor():
    import editor
    return editor

def _get_image_client():
    from derouter import ImageClient
    return ImageClient(
        api_key=config.API_KEY,
        base_url=config.BASE_URL,
        model=config.MODEL,
    )

def _get_claude_client():
    from claude_client import ClaudeClient
    return ClaudeClient(
        api_key=config.CLAUDE_API_KEY,
        base_url=config.CLAUDE_BASE_URL,
        model=config.CLAUDE_MODEL,
    )

def _get_voice_client(voice_id=None):
    import voice
    return voice.VoiceClient(
        api_key=config.ELEVENLABS_API_KEY,
        model=config.ELEVENLABS_MODEL,
        voice_id=voice_id or config.ELEVENLABS_VOICE_ID,
    )


# --- Pydantic Models ---
class MasterIn(BaseModel):
    master_prompt: str = ""

class CharacterIn(BaseModel):
    name: str
    description: str = ""
    size: Optional[str] = None
    quality: Optional[str] = None

class CharacterBatchIn(BaseModel):
    text: str
    size: Optional[str] = None
    quality: Optional[str] = None

class GenerateIn(BaseModel):
    prompt: str = ""
    size: Optional[str] = None
    quality: Optional[str] = None

class StyleFramesIn(BaseModel):
    urls: List[str] = []

class AnalyseIn(BaseModel):
    image_url: str
    question: str = ""

class ScriptIn(BaseModel):
    text: str = ""

class VoiceSynthIn(BaseModel):
    text: str
    provider: str = "elevenlabs"
    voice_id: Optional[str] = None

class SettingsIn(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    claude_api_key: Optional[str] = None
    claude_base_url: Optional[str] = None
    claude_model: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    default_size: Optional[str] = None
    default_quality: Optional[str] = None


# --- Static files ---
os.makedirs(config.DATA_DIR, exist_ok=True)
app.mount("/data", StaticFiles(directory=config.DATA_DIR), name="data")


# --- Routes: Core ---
@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


@app.get("/api/state")
def api_state():
    return {
        "state": store.load_state(),
        "config": {
            "model": config.MODEL,
            "base_url": config.BASE_URL,
            "has_api_key": bool(config.API_KEY),
            "multi_image_edit": config.MULTI_IMAGE_EDIT,
            "claude_model": config.CLAUDE_MODEL,
            "claude_base_url": config.CLAUDE_BASE_URL,
            "has_claude_key": bool(config.CLAUDE_API_KEY),
            "claude_models": config.CLAUDE_MODELS,
            "default_size": config.DEFAULT_SIZE,
            "default_quality": config.DEFAULT_QUALITY,
            "sizes": config.SUPPORTED_SIZES,
            "qualities": config.SUPPORTED_QUALITIES,
        },
    }


@app.get("/api/health")
def api_health():
    image_status = {"ok": False, "error": "not configured"}
    claude_status = {"ok": False, "error": "not configured"}
    voice_status = {"ok": False, "error": "not configured"}
    try:
        image_status = _get_image_client().ping()
    except Exception as e:
        image_status = {"ok": False, "error": str(e)}
    try:
        claude_status = _get_claude_client().ping()
    except Exception as e:
        claude_status = {"ok": False, "error": str(e)}
    try:
        voice_status = _get_voice_client().ping()
    except Exception as e:
        voice_status = {"ok": False, "error": str(e)}
    return {"image": image_status, "claude": claude_status, "voice": voice_status}


# --- Routes: Master Prompt ---
@app.post("/api/master")
def api_master(m: MasterIn):
    st = store.load_state()
    st["master_prompt"] = m.master_prompt
    store.save_state(st)
    return {"ok": True}


# --- Routes: Video / Frames ---
@app.post("/api/video")
async def api_video(file: UploadFile = File(...), fps: float = Form(1.0), max_frames: int = Form(40)):
    import video as videomod
    dest = os.path.join(store.UPLOADS_DIR, store.new_id("upload") + "_" + (file.filename or "video.mp4"))
    with open(dest, "wb") as f:
        f.write(await file.read())
    try:
        urls = videomod.extract_frames(dest, fps=fps, max_frames=max_frames)
    except Exception as e:
        raise HTTPException(500, f"Frame extraction failed: {e}")
    return {"frames": urls, "video_path": dest}


@app.post("/api/style-frames")
def api_style_frames(s: StyleFramesIn):
    st = store.load_state()
    st["style_frames"] = [{"id": store.new_id("frame"), "url": u} for u in s.urls]
    store.save_state(st)
    return {"ok": True, "count": len(st["style_frames"])}


@app.post("/api/scene-detect")
async def api_scene_detect(file: UploadFile = File(...), threshold: float = Form(0.4)):
    editor = _get_editor()
    dest = os.path.join(store.UPLOADS_DIR, store.new_id("scene") + "_" + (file.filename or "video.mp4"))
    with open(dest, "wb") as f:
        f.write(await file.read())
    try:
        times = editor.detect_scenes(dest, threshold=threshold)
        dur = editor.probe_duration(dest)
    except Exception as e:
        raise HTTPException(500, f"Scene detection failed: {e}")
    return {"scene_changes": times, "duration": dur, "video_path": dest}


# --- Routes: Characters ---
@app.post("/api/characters")
def api_create_character(c: CharacterIn):
    if not c.name.strip():
        raise HTTPException(400, "Name is required")
    pipeline = _get_pipeline()
    st = store.load_state()
    client = _get_image_client()
    prompt = pipeline.build_sheet_prompt(st.get("master_prompt", ""), c.name, c.description)
    try:
        img = client.generate(prompt, size=c.size or config.DEFAULT_SIZE, quality=c.quality or config.DEFAULT_QUALITY)
    except Exception as e:
        raise HTTPException(500, f"Sheet generation failed: {e}")
    rec = {
        "id": store.new_id("char"),
        "name": c.name.strip(),
        "description": c.description.strip(),
        "sheet_url": store.write_image("characters", img),
        "prompt": prompt,
        "source": "generated",
        "created": store.now(),
    }
    st.setdefault("characters", []).append(rec)
    store.save_state(st)
    return rec


@app.post("/api/characters/batch")
def api_create_characters_batch(b: CharacterBatchIn):
    pipeline = _get_pipeline()
    entries = pipeline.parse_character_batch(b.text)
    if not entries:
        raise HTTPException(400, "No character entries found")
    st = store.load_state()
    client = _get_image_client()
    out = []
    for entry in entries:
        prompt = pipeline.build_sheet_prompt(st.get("master_prompt", ""), entry["name"], entry["description"])
        try:
            img = client.generate(prompt, size=b.size or config.DEFAULT_SIZE, quality=b.quality or config.DEFAULT_QUALITY)
        except Exception as e:
            raise HTTPException(500, f"Sheet generation failed for {entry['name']}: {e}")
        rec = {
            "id": store.new_id("char"),
            "name": entry["name"].strip(),
            "description": entry["description"].strip(),
            "sheet_url": store.write_image("characters", img),
            "prompt": prompt,
            "source": "generated",
            "created": store.now(),
        }
        st.setdefault("characters", []).append(rec)
        out.append(rec)
    store.save_state(st)
    return out


@app.post("/api/characters/upload")
async def api_upload_character(file: UploadFile = File(...), name: str = Form(...), description: str = Form("")):
    contents = await file.read()
    ext = os.path.splitext(file.filename or "sheet.png")[1]
    path = store.write_bytes(os.path.join("characters", name), contents, ext=ext)
    st = store.load_state()
    rec = {
        "id": store.new_id("char"),
        "name": name,
        "description": description,
        "sheet_url": path,
        "source": "upload",
        "created": store.now(),
    }
    st.setdefault("characters", []).append(rec)
    store.save_state(st)
    return rec


# --- Routes: Image Generation ---
@app.post("/api/generate")
def api_generate(g: GenerateIn):
    pipeline = _get_pipeline()
    st = store.load_state()
    client = _get_image_client()
    final_prompt = g.prompt or pipeline.build_sequence_prompt(
        st.get("master_prompt", ""),
        st.get("style_frames", []),
        st.get("characters", []),
        "",
    )
    try:
        img = client.generate(final_prompt, size=g.size or config.DEFAULT_SIZE, quality=g.quality or config.DEFAULT_QUALITY)
    except Exception as e:
        raise HTTPException(500, f"Generate failed: {e}")
    rec = {
        "id": store.new_id("frame"),
        "url": store.write_image("images", img),
        "prompt": final_prompt,
        "created": store.now(),
    }
    st.setdefault("generated_images", []).append(rec)
    store.save_state(st)
    return rec


# --- Routes: Scene Analysis ---
@app.post("/api/analyse-scene")
def api_analyse_scene(a: AnalyseIn):
    pipeline = _get_pipeline()
    try:
        img = store.read_image(a.image_url)
    except Exception as e:
        raise HTTPException(400, f"Unreadable image: {e}")
    try:
        text = _get_claude_client().analyse_scene(pipeline.downsize_for_vision(img), a.question)
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {e}")
    return {"analysis": text}


# --- Routes: Script ---
@app.post("/api/script")
def api_script(s: ScriptIn):
    if not s.text.strip():
        raise HTTPException(400, "Script text is required")
    try:
        client = _get_claude_client()
        result = client.generate_script(s.text)
        return {"scenes": result}
    except Exception as e:
        raise HTTPException(500, f"Script generation failed: {e}")


# --- Routes: Voice / TTS ---
@app.post("/api/voice/synthesize")
def api_voice_synth(v: VoiceSynthIn):
    if not v.text.strip():
        raise HTTPException(400, "Text is required")
    try:
        client = _get_voice_client(v.voice_id)
        audio_path = client.synthesize(v.text)
        return {"url": audio_path}
    except Exception as e:
        raise HTTPException(500, f"TTS failed: {e}")


# --- Routes: Video Assembly ---
@app.post("/api/assemble")
def api_assemble():
    editor = _get_editor()
    st = store.load_state()
    images = st.get("generated_images", [])
    if not images:
        raise HTTPException(400, "No frames to assemble")
    try:
        video_path = editor.assemble_video(
            [img["url"] for img in images],
            output_dir=config.DATA_DIR,
        )
        return {"url": video_path}
    except Exception as e:
        raise HTTPException(500, f"Assembly failed: {e}")


# --- Routes: Settings ---
@app.post("/api/settings")
def api_settings(s: SettingsIn):
    """Save settings to .env file and reload config."""
    updates = {}
    if s.api_key: updates["DEROUTER_API_KEY"] = s.api_key
    if s.base_url: updates["DEROUTER_BASE_URL"] = s.base_url
    if s.model: updates["IMAGE_MODEL"] = s.model
    if s.claude_api_key: updates["CLAUDE_API_KEY"] = s.claude_api_key
    if s.claude_base_url: updates["CLAUDE_BASE_URL"] = s.claude_base_url
    if s.claude_model: updates["CLAUDE_MODEL"] = s.claude_model
    if s.elevenlabs_api_key: updates["ELEVENLABS_API_KEY"] = s.elevenlabs_api_key
    if s.elevenlabs_voice_id: updates["ELEVENLABS_VOICE_ID"] = s.elevenlabs_voice_id
    if s.default_size: updates["DEFAULT_SIZE"] = s.default_size
    if s.default_quality: updates["DEFAULT_QUALITY"] = s.default_quality
    # Apply to environment
    for k, v in updates.items():
        os.environ[k] = v
    # Reload config module
    import importlib
    importlib.reload(config)
    return {"ok": True}
