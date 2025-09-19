"""
Offline English to Vietnamese Translator using MarianMT
Singleton translator with background prefetch for CPU-friendly translation
"""
from __future__ import annotations
import os
import threading
import re
import logging
from typing import Optional, List

import torch
from transformers import MarianMTModel, MarianTokenizer
from transformers.utils import logging as hf_logging

# Silence noisy HF logs
hf_logging.set_verbosity_error()

logger = logging.getLogger(__name__)

# Global singleton state
_LOCK = threading.Lock()
_READY = threading.Event()
_ERR: Optional[str] = None
_MODEL = _TOK = None

# Cache setup
_CACHE_DIR = os.getenv("HF_HOME") or os.path.join(os.getcwd(), ".hf_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

# Model configuration
MODEL_ID = os.getenv("TRANSLATOR_MODEL_ID", "Helsinki-NLP/opus-mt-en-vi")

# Dependency tracking
_DEPS_CHECKED = False
_DEPS_ERROR_LOGGED = False

def _check_deps():
    """Check if required dependencies are available"""
    try:
        import sentencepiece  # required by MarianTokenizer
        import sacremoses     # required by MarianTokenizer for some models
        return True, None
    except ImportError as e:
        return False, f"SentencePiece/Sacremoses missing: {e}"
    except Exception as e:
        return False, f"Dependency check failed: {e}"

def deps_ok() -> bool:
    """Check if translator dependencies are satisfied"""
    ok, _ = _check_deps()
    return ok

def _load_once(device: str = "cpu"):
    """Load translator model once per process with thread safety"""
    global _MODEL, _TOK, _ERR, _DEPS_ERROR_LOGGED
    
    if _READY.is_set():
        return
    
    with _LOCK:
        if _READY.is_set():
            return
        
        # Check dependencies first
        ok, why = _check_deps()
        if not ok:
            _ERR = why
            # Only log once to avoid spam
            if not _DEPS_ERROR_LOGGED:
                logger.error(f"❌ Translator dependencies missing: {why}")
                _DEPS_ERROR_LOGGED = True
            return  # don't attempt load
        
        _ERR = None
        try:
            logger.info(f"🌐 Loading translator model: {MODEL_ID}")
            
            _TOK = MarianTokenizer.from_pretrained(
                MODEL_ID, 
                cache_dir=_CACHE_DIR, 
                local_files_only=False
            )
            
            _MODEL = MarianMTModel.from_pretrained(
                MODEL_ID, 
                cache_dir=_CACHE_DIR, 
                local_files_only=False
            )
            
            _MODEL.to(device)  # CPU is fine for Marian
            _MODEL.eval()
            
            # Apply INT8 dynamic quantization on CPU for performance
            if device == "cpu":
                try:
                    from torch.ao.quantization import quantize_dynamic
                    _MODEL = quantize_dynamic(_MODEL, {torch.nn.Linear}, dtype=torch.qint8)
                    logger.info("🚀 Translator model quantized to INT8 for CPU acceleration")
                except Exception as e:
                    logger.warning(f"⚠️ Translator quantization failed: {e}")
            
            _READY.set()
            logger.info(f"✅ Translator ready: {MODEL_ID} on {device}")
            
        except Exception as e:
            _ERR = str(e)
            # Only log detailed error once to avoid spam
            if not _DEPS_ERROR_LOGGED:
                logger.error(f"❌ Translator loading failed: {e}")
                _DEPS_ERROR_LOGGED = True

def prefetch_translator_async(device: str = "cpu"):
    """Start background translator loading if not already ready"""
    if _READY.is_set():
        logger.info("📋 Translator already loaded")
        return
    
    logger.info(f"🚀 Starting background translator prefetch: {MODEL_ID}")
    threading.Thread(target=_load_once, args=(device,), daemon=True).start()

def is_ready() -> bool:
    """Check if translator is ready for use"""
    return _READY.is_set()

def last_error() -> Optional[str]:
    """Get last translator loading error if any"""
    return _ERR

def translate_en_to_vi(text: str, max_len: int = 256) -> Optional[str]:
    """
    Translate English text to Vietnamese
    Returns None if translator not ready or on error
    """
    # Return None if not ready or empty text
    if not _READY.is_set() or not text or not text.strip():
        return None
    
    try:
        # Split long text into smaller segments by punctuation
        parts = []
        cur = ""
        
        # Split on sentence boundaries
        for tok in re.split(r"([\.!?;,])", text):
            if not tok:
                continue
                
            cur += tok
            
            # Create segment when we hit punctuation or exceed max length
            if tok in ".!?;," or len(cur) >= max_len:
                segment = cur.strip()
                if segment:
                    parts.append(segment)
                cur = ""
        
        # Add remaining text if any
        if cur.strip():
            parts.append(cur.strip())
        
        # If no parts, translate the whole text
        if not parts:
            parts = [text.strip()]
        
        # Translate each segment
        outs: List[str] = []
        for seg in parts:
            if not seg:
                continue
                
            inputs = _TOK([seg], return_tensors="pt", padding=True).to(_MODEL.device)
            
            with torch.no_grad():
                gen = _MODEL.generate(
                    **inputs, 
                    max_new_tokens=180, 
                    num_beams=3,
                    early_stopping=True
                )
            
            vi = _TOK.decode(gen[0], skip_special_tokens=True).strip()
            if vi:
                outs.append(vi)
        
        result = " ".join(outs).strip()
        return result if result else None
        
    except Exception as e:
        logger.warning(f"⚠️ Translation failed: {e}")
        return None

def get_translator_info() -> dict:
    """Get current translator information"""
    deps_status, deps_error = _check_deps()
    return {
        "model_id": MODEL_ID,
        "ready": _READY.is_set(),
        "deps_ok": deps_status,
        "error": _ERR,
        "deps_error": deps_error,
        "cache_dir": _CACHE_DIR
    }