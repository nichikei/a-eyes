"""
Robust Singleton Caption Pipeline
Single model load per process with background prefetch and graceful fallback
Enhanced with INT8 quantization and perceptual hash gating
"""
from __future__ import annotations
import os
import threading
import torch
import numpy as np
import logging
from typing import Optional, List, Tuple
from PIL import Image
import imagehash
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
from transformers.utils import logging as hf_logging

# Silence noisy HF logs
hf_logging.set_verbosity_error()

from model_registry import choose_caption_model, BLIP_BASE, VITGPT2

logger = logging.getLogger(__name__)

# Global singleton state
_CAPTION_LOCK = threading.Lock()
_CAPTION_READY = threading.Event()
_CAPTION_ERR: Optional[str] = None
_CAPTION_MODEL_ID: Optional[str] = None

# Model instances
_BLIP_PROC = _BLIP_MODEL = None
_VITGPT2_MODEL = _VITGPT2_PROC = _VITGPT2_TOKEN = None

# Cache setup
_CACHE_DIR = os.getenv("HF_HOME") or os.path.join(os.getcwd(), ".hf_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

# Perceptual hash tracking for frame gating
_PHASH_LAST, _OBJ_SIG_LAST = None, None

# Safe word mapper for Vietnamese
SAFE_WORD_MAP = {
    "background": "phông nền",
    "border": "viền", 
    "black": "màu đen",
    "white": "màu trắng",
    "red": "màu đỏ",
    "blue": "màu xanh dương",
    "green": "màu xanh lá",
    "yellow": "màu vàng",
    "brown": "màu nâu",
    "gray": "màu xám",
    "grey": "màu xám",
    "pink": "màu hồng",
    "purple": "màu tím",
    "orange": "màu cam"
}

import re
_pat = re.compile(r"\b(" + "|".join(map(re.escape, SAFE_WORD_MAP.keys())) + r")\b", re.I)

def safe_en2vi_words(s: str) -> str:
    """Replace English color/object words with Vietnamese equivalents"""
    if not s:
        return s
    return _pat.sub(lambda m: SAFE_WORD_MAP[m.group(0).lower()], s)

def frame_signature(img: Image.Image, labels: List[str]) -> Tuple[str, str]:
    """Generate perceptual hash and object signature for frame gating"""
    try:
        sig = str(imagehash.phash(img.convert("RGB")))
        obj = ",".join(sorted(labels))[:64]
        return sig, obj
    except Exception:
        return "", ""

def near_same(sig_now: str, sig_prev: Optional[str], max_hd: int = 4) -> bool:
    """Check if two phash signatures are near-identical (hamming distance)"""
    if not sig_prev or not sig_now:
        return False
    # Hamming distance between hex hashes
    try:
        return sum(a != b for a, b in zip(sig_now, sig_prev)) <= max_hd
    except Exception:
        return False

def post_process_vietnamese(text: str) -> str:
    """Post-process Vietnamese text with light polish and safe word mapping"""
    if not text:
        return text
    
    # Apply safe word mapping for specific nouns/adjectives
    s = safe_en2vi_words(text)
    
    # Light VN polish
    s = s.replace("  ", " ").strip().rstrip(".") + "."
    s = s.replace(" màu màu", " màu")
    
    return s

def _load_once(device: str):
    """Load caption model once per process with thread safety"""
    global _CAPTION_MODEL_ID, _CAPTION_ERR
    global _BLIP_PROC, _BLIP_MODEL, _VITGPT2_MODEL, _VITGPT2_PROC, _VITGPT2_TOKEN

    if _CAPTION_READY.is_set():
        return

    with _CAPTION_LOCK:
        if _CAPTION_READY.is_set():
            return
        
        _CAPTION_ERR = None
        try:
            model_id = choose_caption_model()
            _CAPTION_MODEL_ID = model_id
            
            logger.info(f"📥 Loading caption model once: {model_id}")

            if model_id == BLIP_BASE:
                proc = BlipProcessor.from_pretrained(
                    model_id, 
                    use_fast=True, 
                    cache_dir=_CACHE_DIR, 
                    local_files_only=False, 
                    trust_remote_code=False
                )
                mdl = BlipForConditionalGeneration.from_pretrained(
                    model_id, 
                    cache_dir=_CACHE_DIR, 
                    local_files_only=False, 
                    trust_remote_code=False
                ).to(device).eval()
                
                # Apply INT8 dynamic quantization on CPU for performance
                if device == "cpu":
                    try:
                        from torch.ao.quantization import quantize_dynamic
                        mdl = quantize_dynamic(mdl, {torch.nn.Linear}, dtype=torch.qint8)
                        logger.info("🚀 BLIP model quantized to INT8 for CPU acceleration")
                    except Exception as e:
                        logger.warning(f"⚠️ BLIP quantization failed: {e}")
                
                _BLIP_PROC, _BLIP_MODEL = proc, mdl
                logger.info(f"✅ BLIP model loaded successfully on {device}")

            elif model_id == VITGPT2:
                proc = ViTImageProcessor.from_pretrained(
                    model_id, 
                    cache_dir=_CACHE_DIR, 
                    local_files_only=False
                )
                tok = AutoTokenizer.from_pretrained(
                    model_id, 
                    cache_dir=_CACHE_DIR, 
                    local_files_only=False
                )
                mdl = VisionEncoderDecoderModel.from_pretrained(
                    model_id, 
                    cache_dir=_CACHE_DIR, 
                    local_files_only=False
                ).to(device).eval()
                
                # Apply INT8 dynamic quantization on CPU for performance
                if device == "cpu":
                    try:
                        from torch.ao.quantization import quantize_dynamic
                        mdl = quantize_dynamic(mdl, {torch.nn.Linear}, dtype=torch.qint8)
                        logger.info("🚀 VIT-GPT2 model quantized to INT8 for CPU acceleration")
                    except Exception as e:
                        logger.warning(f"⚠️ VIT-GPT2 quantization failed: {e}")
                
                _VITGPT2_MODEL, _VITGPT2_PROC, _VITGPT2_TOKEN = mdl, proc, tok
                logger.info(f"✅ VIT-GPT2 model loaded successfully on {device}")

            _CAPTION_READY.set()
            logger.info("🎉 Caption model ready for inference")
            
        except Exception as e:
            _CAPTION_ERR = str(e)
            logger.error(f"❌ Caption model loading failed: {e}")
            # don't set READY; allow future retries

def prefetch_caption_model_async(device: str):
    """Start background model loading if not already ready"""
    if _CAPTION_READY.is_set():
        logger.info("📋 Caption model already loaded")
        return
    
    logger.info(f"🚀 Starting background caption model prefetch on {device}")
    threading.Thread(target=_load_once, args=(device,), daemon=True).start()

def _downscale_short_side(img: Image.Image, short: int = 384) -> Image.Image:
    """Downscale image to reduce memory usage"""
    w, h = img.size
    if min(w, h) <= short:
        return img
    
    if w < h:
        new_w, new_h = short, int(h * short / w)
    else:
        new_h, new_w = short, int(w * short / h)
    
    return img.resize((new_w, new_h), Image.LANCZOS)

def generate_caption(image: Image.Image, device: str, max_new_tokens: int = 30) -> Optional[str]:
    """
    Generate caption using loaded model or return None if not ready
    This allows graceful fallback to heuristic captions
    """
    # If not ready yet, return None so caller can keep heuristic result
    if not _CAPTION_READY.is_set():
        return None

    try:
        img = _downscale_short_side(image, 384)
        
        if _CAPTION_MODEL_ID == BLIP_BASE and _BLIP_MODEL is not None:
            inputs = _BLIP_PROC(img, return_tensors="pt").to(device)
            with torch.no_grad():
                out = _BLIP_MODEL.generate(**inputs, max_new_tokens=max_new_tokens)
            txt = _BLIP_PROC.decode(out[0], skip_special_tokens=True).strip()
            return txt

        if _CAPTION_MODEL_ID == VITGPT2 and _VITGPT2_MODEL is not None:
            pixel = _VITGPT2_PROC(images=img, return_tensors="pt").to(device)
            with torch.no_grad():
                out = _VITGPT2_MODEL.generate(**pixel, max_new_tokens=max_new_tokens)
            txt = _VITGPT2_TOKEN.decode(out[0], skip_special_tokens=True).strip()
            return txt

        return None
        
    except Exception as e:
        logger.warning(f"⚠️ Caption generation failed: {e}")
        return None

def last_caption_error() -> Optional[str]:
    """Get last caption loading error if any"""
    return _CAPTION_ERR

def is_caption_ready() -> bool:
    """Check if caption model is ready for inference"""
    return _CAPTION_READY.is_set()

def get_model_info() -> dict:
    """Get current model information"""
    return {
        "model_id": _CAPTION_MODEL_ID,
        "ready": _CAPTION_READY.is_set(),
        "error": _CAPTION_ERR,
        "cache_dir": _CACHE_DIR
    }

# Legacy compatibility for existing code
class OptimizedSceneDescriber:
    """Legacy compatibility wrapper"""
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        
    def generate(self, image: Image.Image, objects: List[str] = None) -> Optional[str]:
        """Generate caption with fallback to heuristic"""
        caption = generate_caption(image, self.device)
        if caption:
            return safe_en2vi_words(caption)
        return None
    
    def object_list_to_vn(self, objects: tuple) -> str:
        """Convert object list to Vietnamese description"""
        if not objects:
            return "không có vật thể nào"
        
        obj_count = {}
        for obj in objects:
            obj_count[obj] = obj_count.get(obj, 0) + 1
        
        vn_parts = []
        for obj, count in obj_count.items():
            if count == 1:
                vn_parts.append(f"một {obj}")
            else:
                vn_parts.append(f"{count} {obj}")
        
        if len(vn_parts) == 1:
            return vn_parts[0]
        elif len(vn_parts) == 2:
            return f"{vn_parts[0]} và {vn_parts[1]}"
        else:
            return f"{', '.join(vn_parts[:-1])} và {vn_parts[-1]}"