# simple_yolo_backend.py
# High-performance YOLO backend (heuristic-only, VN TTS)
# - Robust object filtering (per-class conf & min area)
# - Clock-face location + size + distance
# - Reliable TTS (blocking), dedupe repeated speech
# - Smart fallback (optional)

from __future__ import annotations
import os

# Stable HF cache
os.environ.setdefault("HF_HOME", os.path.join(os.getcwd(), ".hf_cache"))
os.makedirs(os.environ["HF_HOME"], exist_ok=True)

# Silence transformers logs (if any submodule uses it)
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import cv2
import numpy as np
import base64
import io
from PIL import Image
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("tts_vn").setLevel(logging.DEBUG)

# ---------- Optional runtime diag ----------
try:
    from runtime_diag import assert_torch_from_venv, pick_device, log_torch_env
except Exception:
    def assert_torch_from_venv(strict=True): return True
    def pick_device(): return "cpu"
    def log_torch_env(_): return {}

# ---------- Optional smart fallback ----------
try:
    from smart_fallback import smart_fallback_detection
    SMART_FALLBACK = True
    logger.info("✅ Smart fallback detection available")
except Exception:
    SMART_FALLBACK = False

# ---------- Heuristic captioning (NEW) ----------
from captioning_heuristic import (
    improved_heuristic_caption, normalize_bbox, vi_label, size_adj, range_text, clock_pos
)

# ---------- Enhanced Detection System (NEW) ----------
try:
    from enhanced_detection import process_enhanced_detection, ImagePreprocessor
    ENHANCED_DETECTION = True
    logger.info("✅ Enhanced detection system available")
except Exception as e:
    logger.warning(f"⚠️ Enhanced detection not available: {e}")
    ENHANCED_DETECTION = False
    def process_enhanced_detection(dets, img=None):
        return dets

# ---------- TTS ----------
# tts_vn is preferred; if it is missing or fails, speech falls back to
# Windows SAPI + OneCore voices (Microsoft An) below.
try:
    from tts_vn import speak_vn_blocking, current_voice_info
except Exception as e:
    logger.warning(f"⚠️ tts_vn not available: {e}")
    def speak_vn_blocking(txt: str, *args, **kwargs):
        raise RuntimeError("tts_vn unavailable")
    def current_voice_info():
        return {"error": "tts_vn module not available"}

# SAPI is Windows-only. Without comtypes every SAPI helper below fails inside
# its own try/except and reports "no voice", so the server still runs (and
# the test suite still imports it) on Linux/macOS.
try:
    import comtypes, comtypes.client
except Exception:
    comtypes = None

def _enum_sapi_desktop():
    names = []
    try:
        sp = comtypes.client.CreateObject("SAPI.SpVoice")
        toks = sp.GetVoices()
        for i in range(toks.Count):
            names.append(toks.Item(i).GetDescription())
    except Exception:
        pass
    return names

def _enum_onecore(hive="HKLM"):
    names = []
    try:
        cat = comtypes.client.CreateObject("SAPI.SpObjectTokenCategory")
        if hive.upper() == "HKCU":
            cat.SetId(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Speech_OneCore\Voices")
        else:
            cat.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices")
        toks = cat.EnumerateTokens()
        for i in range(toks.Count):
            names.append(toks.Item(i).GetDescription())
    except Exception:
        pass
    return names

def _pick_onecore_token(hint_name="", hint_lang="vi"):
    """Trả về token giọng OneCore (ưu tiên HKCU rồi HKLM) hoặc None."""
    hint_name = (hint_name or "").lower()
    hint_lang = (hint_lang or "vi").lower()
    for hive in ("HKCU", "HKLM"):
        try:
            cat = comtypes.client.CreateObject("SAPI.SpObjectTokenCategory")
            if hive == "HKCU":
                cat.SetId(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Speech_OneCore\Voices")
            else:
                cat.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices")
            toks = cat.EnumerateTokens()

            # Ưu tiên theo tên
            if hint_name:
                for i in range(toks.Count):
                    t = toks.Item(i)
                    d = t.GetDescription().lower()
                    if hint_name in d:
                        return t, d

            # Sau đó theo ngôn ngữ "vi"
            for i in range(toks.Count):
                t = toks.Item(i)
                d = t.GetDescription().lower()
                if ("viet" in d) or ("vi-vn" in d) or (hint_lang in d):
                    return t, d
        except Exception:
            pass
    return None, None

def _sapi_select_vi_voice(sp):
    """Chọn giọng Việt cho SpVoice, trả về (bool_chosen, desc)."""
    # 1) OneCore (HKCU/HKLM) - ưu tiên tìm giọng Việt
    token, desc = _pick_onecore_token(
        hint_name=os.getenv("TTS_VOICE_NAME", "an"),  # Tìm giọng An
        hint_lang="vi"
    )
    if token is not None:
        try:
            sp.Voice = token
            logger.info(f"[TTS] OneCore Vietnamese selected: {desc}")
            return True, desc
        except Exception as e:
            logger.warning(f"[TTS] OneCore set failed: {e}")

    # 2) Desktop - tìm giọng Việt
    try:
        toks = sp.GetVoices()
        # Ưu tiên tìm các giọng Việt Nam
        vietnamese_voices = []
        for i in range(toks.Count):
            voice = toks.Item(i)
            desc = voice.GetDescription().lower()
            if any(keyword in desc for keyword in ["viet", "vi-vn", "vietnam", "an", "linh"]):
                vietnamese_voices.append((voice, desc))
        
        if vietnamese_voices:
            # Chọn giọng Việt đầu tiên
            voice, desc = vietnamese_voices[0]
            sp.Voice = voice
            logger.info(f"[TTS] Vietnamese voice selected: {desc}")
            return True, desc
    except Exception as e:
        logger.warning(f"[TTS] Desktop voice selection failed: {e}")

    # 3) Fallback - chọn giọng đầu tiên nhưng cảnh báo
    try:
        toks = sp.GetVoices()
        if toks.Count > 0:
            voice = toks.Item(0)
            desc = voice.GetDescription()
            sp.Voice = voice
            logger.warning(f"[TTS] No Vietnamese voice found, using fallback: {desc}")
            return True, desc
    except Exception as e:
        logger.error(f"[TTS] All voice selection failed: {e}")

    return False, None

def _sapi_say_blocking(text: str) -> bool:
    try:
        comtypes.CoInitialize()
        try:
            sp = comtypes.client.CreateObject("SAPI.SpVoice")
            sp.Volume = int(os.getenv("TTS_VOLUME", "100"))
            sp.Rate   = int(os.getenv("TTS_RATE", "0"))

            ok, chosen = _sapi_select_vi_voice(sp)
            if not ok:
                logger.warning("[TTS] No VI voice found; using whatever is available.")
            else:
                logger.info(f"[TTS] Using voice: {chosen}")

            # Force Vietnamese pronunciation with enhanced SSML
            try:
                # Enhanced SSML with Vietnamese language and phonetic hints
                ssml_text = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="vi-VN">
                    <voice xml:lang="vi-VN">
                        <prosody rate="medium" pitch="medium">
                            {text}
                        </prosody>
                    </voice>
                </speak>'''
                sp.Speak(ssml_text, 8)  # SPF_IS_XML = 8
                logger.info(f"[TTS] Vietnamese SSML spoken: {text[:50]}...")
                return True
            except Exception as e:
                logger.warning(f"[TTS] SSML failed: {e}")
                
            # Fallback với text thường nhưng vẫn force Vietnamese context
            try:
                # Set language property if available
                sp.Speak(text, 0)  # SPF_DEFAULT = 0
                logger.info(f"[TTS] Vietnamese text spoken: {text[:50]}...")
                return True
            except Exception as e:
                logger.error(f"[TTS] All speech attempts failed: {e}")
                return False
        finally:
            try: comtypes.CoUninitialize()
            except Exception: pass
    except Exception as e:
        logger.error(f"❌ SAPI speak failed: {e}")
        return False

DISABLE_TTS_DEDUPE = os.getenv("DISABLE_TTS_DEDUPE", "0") == "1"
ALWAYS_SPEAK = os.getenv("ALWAYS_SPEAK", "0") == "1"  # ✅ Tắt mặc định để tránh TTS kép

# ---------- YOLO Detector ----------
detector = None
selected_device = "cpu"
startup_complete = False
startup_time = 0.0

# ---------- Filters / thresholds ----------
MIN_AREA_RATIO = float(os.getenv("MIN_AREA_RATIO", "0.003"))  # 0.3%

PER_CLASS_MIN_CONF: Dict[str, float] = {
    "person": 0.15,
    "cat": 0.45,
    "dog": 0.40,
    "potted plant": 0.35,
    "toothbrush": 0.45,
}
DEFAULT_MIN_CONF = float(os.getenv("DEFAULT_MIN_CONF", "0.25"))

# ---------- TTS dedupe ----------
_last_spoken_text: Optional[str] = None

def should_speak(text: str) -> bool:
    if DISABLE_TTS_DEDUPE:
        return True
    global _last_spoken_text
    text = (text or "").strip()
    if not text:
        return False
    if _last_spoken_text and _last_spoken_text == text:
        logger.debug("[TTS] Skipped duplicate sentence.")
        return False
    _last_spoken_text = text
    return True

# ---------- Models ----------
class DescribeRequest(BaseModel):
    image: str
    autoSpeak: bool = True
    fastFirst: bool = True

class ObjectDetail(BaseModel):
    en: str
    vi: str
    conf: float
    area_ratio: float
    clock: str
    size_text: str
    range_text: str

class DescribeResponse(BaseModel):
    caption_fast: str
    confidence: float
    count: int
    objects: List[str]
    objects_detail: List[ObjectDetail]
    processing_time_ms: int
    # Per-stage breakdown (decode / detect / caption), for profiling.
    timings_ms: Dict[str, float] = {}

# ---------- Utils ----------
def decode_base64_image(image_data: str) -> np.ndarray:
    try:
        if image_data.startswith("data:image/"):
            image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return cv_image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

def _class_min_conf(label_en: str) -> float:
    le = (label_en or "").lower()
    return PER_CLASS_MIN_CONF.get(le, DEFAULT_MIN_CONF)

def _filter_and_prepare(dets: List[Dict], W: int, H: int) -> List[Dict]:
    out = []
    for d in dets or []:
        en = d.get("label_en", d.get("label", d.get("class_name", "")))
        conf = float(d.get("confidence", d.get("conf", 0.0)))
        bbox = d.get("bbox")
        if bbox is None:
            if all(k in d for k in ("x1","y1","x2","y2")):
                bbox = [d["x1"], d["y1"], d["x2"], d["y2"]]
            elif all(k in d for k in ("x","y","w","h")):
                bbox = [d["x"], d["y"], d["x"]+d["w"], d["y"]+d["h"]]
        if bbox is None:
            continue

        nb = normalize_bbox({"label": en, "bbox": bbox, "confidence": conf}, W, H)
        if not nb:
            continue

        # Enhanced detection may have already applied confidence optimization
        validation_score = d.get("validation_score", 0.0)
        if validation_score > 0:
            # Use enhanced validation score instead of basic confidence filtering
            min_validation_score = 0.3
            if validation_score < min_validation_score:
                continue
        else:
            # Fallback to traditional confidence filtering
            if conf < _class_min_conf(en):
                continue
            
        if nb["area_ratio"] < MIN_AREA_RATIO:
            continue

        out.append({
            "en": (en or "").lower(),
            "vi": vi_label(en),
            "conf": conf,
            "bbox": [nb["x1"], nb["y1"], nb["x2"], nb["y2"]],
            "cx": nb["cx"], "cy": nb["cy"],
            "area_ratio": nb["area_ratio"],
            "clock": clock_pos(nb["cx"], nb["cy"], W, H),
            "size_text": size_adj(nb["area_ratio"]),
            "range_text": range_text(nb["area_ratio"]),
            "validation_score": d.get("validation_score", conf)  # Include validation score
        })
    out.sort(key=lambda o: -o["area_ratio"])
    return out

# ---------- FastAPI ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event()
    yield

app = FastAPI(
    title="AI Eyes YOLO Backend (Heuristic+VN TTS)",
    version="2.3.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

async def startup_event():
    global detector, selected_device, startup_complete, startup_time
    t0 = time.time()
    logger.info("🚀 Starting high-performance warmup...")
    try:
        log_torch_env(logger)
        strict = os.getenv("STRICT_VENV_TORCH", "1") != "0"
        assert_torch_from_venv(strict=strict)
        logger.info("✅ PyTorch venv validation passed")
    except Exception as e:
        logger.warning(f"⚠️ Torch venv check: {e}")

    try:
        selected_device = pick_device()
    except Exception:
        selected_device = "cpu"
    logger.info(f"🖥️ Using device: {selected_device}")

    # Init YOLO
    try:
        from app.detector import Detector
        logger.info("🔍 Initializing YOLO detector...")
        # Prefer an OpenVINO export when present: ~7x faster on Intel CPUs
        # (see scripts/benchmark.py). Override with YOLO_MODEL.
        default_model = "yolov5su_openvino_model" if os.path.isdir("yolov5su_openvino_model") else "yolov5su.pt"
        detector = Detector(os.getenv("YOLO_MODEL", default_model), device=selected_device)
        if getattr(detector, "is_loaded", False):
            logger.info("✅ YOLO detector ready")
        else:
            logger.warning("⚠️ YOLO detector failed, will try fallback")
            detector = None
    except Exception as e:
        logger.warning(f"⚠️ Detector init failed: {e}")
        detector = None

    startup_time = (time.time() - t0) * 1000
    startup_complete = True
    logger.info(f"🎉 Startup complete in {startup_time:.1f}ms")
    if SMART_FALLBACK:
        logger.info("✅ Smart fallback detection available")
    logger.info("✅ Enhanced heuristic captioning available")

# ---------- Endpoints ----------
@app.get("/health")
async def health():
    return {
        "status": "healthy" if startup_complete else "warming_up",
        "startup_complete": startup_complete,
        "startup_time_ms": startup_time,
        "device": selected_device,
        "detector_loaded": detector is not None and getattr(detector, "is_loaded", False),
        "enhanced_detection": ENHANCED_DETECTION,
        "min_area_ratio": MIN_AREA_RATIO,
        "per_class_min_conf": PER_CLASS_MIN_CONF,
        "default_min_conf": DEFAULT_MIN_CONF,
        "always_speak": ALWAYS_SPEAK,
    }

@app.get("/enhanced-detection-stats")
async def enhanced_detection_stats():
    """Get enhanced detection system statistics"""
    try:
        if not ENHANCED_DETECTION:
            return {"error": "Enhanced detection not available"}
        
        from enhanced_detection import enhanced_validator, confidence_optimizer
        
        stats = {
            "enhanced_detection_enabled": ENHANCED_DETECTION,
            "history_frames": enhanced_validator.history_frames,
            "min_consecutive_frames": enhanced_validator.min_consecutive_frames,
            "total_frames_processed": enhanced_validator.frame_counter,
            "detection_history_size": len(enhanced_validator.detection_history),
            "confidence_thresholds_count": len(confidence_optimizer.base_thresholds),
            "default_threshold": confidence_optimizer.default_threshold,
            "status": "active"
        }
        
        return stats
    except Exception as e:
        return {"error": f"Failed to get stats: {e}"}

# ---------- TTS Endpoints ----------
@app.get("/tts-voices")
def tts_voices():
    out = {
        "sapi_desktop": _enum_sapi_desktop(),
        "sapi_onecore_hkcu": _enum_onecore("HKCU"),
        "sapi_onecore_hklm": _enum_onecore("HKLM"),
    }
    return out

@app.get("/tts-sapi-test")
def tts_sapi_test(q: str = "Xin chào, đây là kiểm tra giọng nói tiếng Việt qua SAPI."):
    ok = _sapi_say_blocking(q)
    return {"ok": ok, "spoken": q}

@app.get("/status")
async def status():
    return await health()

@app.get("/voice-info")
def voice_info():
    try:
        return current_voice_info()
    except Exception as e:
        return {"error": str(e)}

# Speech runs on one background worker: utterances never overlap, and the HTTP
# response no longer waits for the caption to be read aloud (that used to add
# the whole TTS duration, up to the 7 s worker timeout, to every request).
_tts_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tts")


def _speak_caption(text: str) -> None:
    logger.info(f"[speak] {text}")
    try:
        speak_vn_blocking(text)
        return
    except Exception as e:
        logger.warning(f"tts_vn unavailable or failed: {e}")
    ok = _sapi_say_blocking(text)
    logger.info(f"[sapi-onecore] spoken={ok}")


# A plain ``def`` endpoint: FastAPI runs it in its threadpool, so YOLO
# inference (CPU-bound, ~100 ms) no longer blocks the event loop and /health
# stays responsive while a frame is being processed.
@app.post("/api/describe", response_model=DescribeResponse)
def describe(req: DescribeRequest):
    if not startup_complete:
        raise HTTPException(status_code=503, detail="System warming up. Try again.")

    total_t0 = time.perf_counter()

    # 1) Decode
    t0 = time.perf_counter()
    cv_img = decode_base64_image(req.image)
    H, W = cv_img.shape[:2]
    t_decode = (time.perf_counter() - t0) * 1000
    logger.info(f"📸 Image decoded in {t_decode:.1f}ms: {(H, W, 3)}")

    # 2) Detect with Enhanced Processing
    t0 = time.perf_counter()
    raw_dets: List[Dict] = []
    if detector and getattr(detector, "is_loaded", False):
        try:
            raw_dets = detector.detect(cv_img) or []
            logger.info(f"🤖 YOLO detected {len(raw_dets)} objects")
        except Exception as e:
            logger.warning(f"⚠️ Detector error: {e}")
    elif SMART_FALLBACK:
        try:
            sf = smart_fallback_detection(cv_img) or []
            raw_dets = [{"label": d["label"], "confidence": d["confidence"], "bbox": d.get("bbox", [0,0,0,0])} for d in sf]
            logger.info(f"🔄 Fallback detected {len(raw_dets)} objects")
        except Exception as e:
            logger.warning(f"⚠️ Fallback failed: {e}")

    # Apply Enhanced Detection Processing (skip for auto mode to speed up)
    if ENHANCED_DETECTION and raw_dets and not req.autoSpeak:
        try:
            enhanced_dets = process_enhanced_detection(raw_dets, cv_img)
            logger.info(f"🔍 Enhanced filtering: {len(raw_dets)} → {len(enhanced_dets)}")
            raw_dets = enhanced_dets
        except Exception as e:
            logger.warning(f"⚠️ Enhanced detection failed, using original: {e}")
    elif req.autoSpeak:
        logger.info(f"⚡ Fast mode: skipping enhanced detection for auto mode")

    filtered = _filter_and_prepare(raw_dets, W, H)
    kept = len(filtered)
    t_detect = (time.perf_counter() - t0) * 1000
    logger.info(f"🎯 Detection completed in {t_detect:.1f}ms, kept {kept} objects")

    # 3) Caption - Sử dụng phiên bản cải tiến
    t0 = time.perf_counter()
    caption_dets = [{"label": f["en"], "bbox": f["bbox"], "confidence": f["conf"]} for f in filtered]
    caption_fast = improved_heuristic_caption(caption_dets, W, H) or "Khung hình trống."
    t_cap = (time.perf_counter() - t0) * 1000
    logger.info(f"⚡ Enhanced caption generated in {t_cap:.1f}ms")

    # 4) TTS (non-blocking, see _tts_executor)
    if (ALWAYS_SPEAK or req.autoSpeak) and should_speak(caption_fast):
        _tts_executor.submit(_speak_caption, caption_fast)

    # Response
    objects_en = [f["en"] for f in filtered]
    avg_conf = (sum(f["conf"] for f in filtered) / len(filtered)) if filtered else 0.0
    details_out = [
        ObjectDetail(
            en=f["en"],
            vi=f["vi"],
            conf=float(f"{f['conf']:.3f}"),
            area_ratio=float(f"{f['area_ratio']:.4f}"),
            clock=f["clock"],
            size_text=f["size_text"],
            range_text=f["range_text"],
        )
        for f in filtered
    ]

    total_ms = int((time.perf_counter() - total_t0) * 1000)
    logger.info(f"⚡ Fast response in {total_ms:.1f}ms (decode:{t_decode:.1f}, yolo:{t_detect:.1f}, heuristic:{t_cap:.1f})")

    return DescribeResponse(
        caption_fast=caption_fast,
        confidence=avg_conf,
        count=len(filtered),
        objects=objects_en,
        objects_detail=details_out,
        processing_time_ms=total_ms,
        timings_ms={
            "decode": round(t_decode, 2),
            "detect": round(t_detect, 2),
            "caption": round(t_cap, 2),
        },
    )

# ---------- Main ----------
if __name__ == "__main__":
    print("🚀 Starting Simple YOLO Backend with Smart Fallback...")
    port = int(os.getenv("BACKEND_PORT", "8011"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
