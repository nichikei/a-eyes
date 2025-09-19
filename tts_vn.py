import re, time, queue, threading, logging, pyttsx3
import subprocess, shlex, os, sys, logging
from shutil import which

logger = logging.getLogger(__name__)
SENT_END = r'[\.!?;]'   # NO comma
_MIN_MS_PER_CHAR = 22   # heuristic; adjust 18–25 if needed

def _pick_vn_voice_id(engine=None):
    """Pick best Vietnamese voice, preferring Microsoft An."""
    if engine is None:
        engine = pyttsx3.init()
    
    voices = engine.getProperty('voices')
    
    # Prefer "Microsoft An" first
    for voice in voices:
        name = getattr(voice, 'name', '').lower()
        if 'microsoft an' in name:
            return voice.id
    
    # Then any Vietnamese voice
    for voice in voices:
        voice_id = voice.id.lower()
        name = getattr(voice, 'name', '').lower()
        langs = getattr(voice, 'languages', [])
        
        # Check for Vietnamese indicators
        if any('viet' in x.lower() for x in [voice_id, name] + [str(l) for l in langs]):
            return voice.id
    
    # If no Vietnamese voice, return first available voice as fallback
    if voices:
        return voices[0].id
    
    return None  # No voices at all

def _new_engine():
    """Create new TTS engine with Vietnamese voice preference."""
    # Initialize COM for threading
    try:
        import comtypes
        comtypes.CoInitialize()
    except:
        pass  # May already be initialized
    
    engine = pyttsx3.init()
    
    # Pick Vietnamese voice
    voice_id = _pick_vn_voice_id(engine)
    if voice_id:
        try:
            engine.setProperty('voice', voice_id)
        except Exception as e:
            logger.warning(f"Failed to set voice {voice_id}: {e}")
    
    # Set fast rate
    engine.setProperty('rate', 200)
    return engine

def chunk_caption(text: str, max_len: int = 160):
    s = re.sub(r'\s+', ' ', text or '').strip()
    if not s: return []
    if not re.search(SENT_END + r'$', s): s += '.'
    parts, cur = [], ''
    for tok in re.split(f'({SENT_END})', s):
        if not tok: continue
        cur += tok
        if re.fullmatch(SENT_END, tok):
            parts.append(cur.strip()); cur = ''
    if cur.strip(): parts.append(cur.strip())
    merged = []
    for p in parts:
        # protect clause containing 'khung hình' + 'với kích thước'
        if 'khung hình' in p and 'với kích thước' in p:
            merged.append(p.strip()); continue
        if merged and (len(merged[-1]) < 25 or len(p) < 25) and len(merged[-1] + ' ' + p) <= max_len:
            merged[-1] = (merged[-1] + ' ' + p).strip()
        else:
            if len(p) > max_len:
                buf = ''
                for w in re.split(r'(\s+)', p):
                    if len(buf) + len(w) > max_len and buf:
                        merged.append(buf.strip()); buf = ''
                    buf += w
                if buf.strip(): merged.append(buf.strip())
            else:
                merged.append(p.strip())
    return merged

class AsyncTTSQueue:
    def __init__(self, min_interval_ms: int = 2500, rate: int = 165):
        self.q = queue.Queue(maxsize=64)
        self.min_interval = max(0.0, min_interval_ms/1000.0)
        self._last_norm = ''; self._last_t = 0.0
        self.rate = rate; self._stop = False
        self._logger = logging.getLogger("tts_vn")
        self._worker = threading.Thread(target=self._run, daemon=True); self._worker.start()

    def _init_engine(self):
        return _new_engine()

    def speak(self, text: str, *, disable_debounce: bool = False):
        s = re.sub(r'\s+', ' ', text or '').strip()
        if not s: return
        norm = s.lower(); now = time.time()
        if not disable_debounce:
            if norm == self._last_norm and (now - self._last_t) < self.min_interval: return
        chunks = [s]  # keep whole sentence as one chunk to avoid split
        if self._logger: self._logger.debug(f"[TTS enqueue] {chunks}")
        for seg in chunks:
            try: self.q.put_nowait(seg)
            except queue.Full: break
        self._last_norm, self._last_t = norm, now

    def stop(self):
        self._stop = True
        try: self.q.put_nowait(None)
        except queue.Full: pass

    def _run(self):
        e = self._init_engine()
        while not self._stop:
            item = self.q.get()
            if item is None: break
            try:
                t0 = time.time()
                if self._logger: self._logger.debug(f"[TTS speak] {item}")
                e.say(item); e.runAndWait()
                dur_ms = int((time.time() - t0)*1000)
                # detect clipped: duration too short vs text length
                expected_ms = max(500, len(item) * _MIN_MS_PER_CHAR)
                if dur_ms < expected_ms * 0.55:
                    # retry once with a prosody hint to slow SAPI down
                    hint = item.replace(" với ", " — với ")
                    if self._logger: self._logger.debug(f"[TTS retry] dur={dur_ms}ms < exp={expected_ms}ms -> '{hint}'")
                    e.say(hint); e.runAndWait()
                time.sleep(0.10)
            except Exception:
                try: e = self._init_engine()
                except Exception: pass
            finally:
                self.q.task_done()

_TTSQ = None
def _get_queue():
    global _TTSQ
    if _TTSQ is None: _TTSQ = AsyncTTSQueue()
    return _TTSQ

def speak_vn(text: str, blocking: bool = False, *, disable_debounce: bool = False):
    q = _get_queue()
    if blocking:
        # one-shot blocking with a fresh engine (most reliable path)
        e = _new_engine()
        s = re.sub(r'\s+', ' ', text or '').strip()
        if not s: return
        t0 = time.time()
        e.say(s); e.runAndWait()
        # duration check & retry
        dur_ms = int((time.time() - t0)*1000)
        expected_ms = max(500, len(s) * _MIN_MS_PER_CHAR)
        if dur_ms < expected_ms * 0.55:
            e.say(s.replace(" với ", " — với ")); e.runAndWait()
        return
    else:
        q.speak(text, disable_debounce=disable_debounce)

def speak_vn_raw(text: str):
    """
    Enqueue the WHOLE text as a single chunk (no splitting, no debounce),
    so short fast captions are spoken fully in one go.
    """
    q = _get_queue()
    s = re.sub(r'\s+', ' ', text or '').strip()
    if not s: return
    try:
        if q._logger: q._logger.debug(f"[TTS enqueue RAW] {s}")
    except Exception:
        pass
    try:
        q.q.put_nowait(s)
    except queue.Full:
        pass

# convenience: force-blocking single chunk with standalone COM initialization
def speak_vn_blocking(text: str):
    """Speak text using blocking TTS with COM initialization for reliable single-shot speaking."""
    if not text or not text.strip():
        return
    
    try:
        # Initialize COM for this thread
        import comtypes
        try:
            comtypes.CoInitialize()
        except:
            pass  # May already be initialized
        
        # Create a fresh engine each time for blocking mode
        engine = pyttsx3.init()
        
        # Pick Vietnamese voice
        voice_id = _pick_vn_voice_id(engine)
        if voice_id:
            try:
                engine.setProperty('voice', voice_id)
            except Exception as e:
                logger.warning(f"Failed to set voice {voice_id}: {e}")
        
        # Set fast rate
        engine.setProperty('rate', 200)
        
        # Speak and wait
        t0 = time.time()
        engine.say(text)
        engine.runAndWait()
        dur_ms = int((time.time() - t0) * 1000)
        
        # Detect clipped speech and retry with prosody hint
        expected_ms = max(500, len(text) * _MIN_MS_PER_CHAR)
        if dur_ms < expected_ms * 0.55:
            # Retry with prosody hint
            hint_text = text.replace(" với ", " — với ")
            logger.debug(f"[TTS retry] dur={dur_ms}ms < exp={expected_ms}ms -> retrying")
            engine.say(hint_text)
            engine.runAndWait()
        
        # Clean up
        engine.stop()
        
        try:
            comtypes.CoUninitialize()
        except:
            pass
            
    except Exception as e:
        logger.error(f"TTS blocking error: {e}")
        raise

# add a helper to report chosen voice
def current_voice_info():
    try:
        e = _new_engine()
        vid = e.getProperty("voice")
        rate = e.getProperty("rate")
        return {"voice_id": vid, "rate": rate}
    except Exception:
        return {"voice_id": None, "rate": None}

def stop_tts():
    global _TTSQ
    if _TTSQ: _TTSQ.stop()

import os, sys, subprocess, logging
log = logging.getLogger("tts_vn")

def _py():
    return sys.executable or "python"

def speak_vn_subproc(text: str, timeout_s: float = 7.0) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    worker = os.path.join(os.path.dirname(__file__), "tts_worker.py")
    if not os.path.exists(worker):
        worker = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tts_worker.py"))
    cmd = [_py(), worker, s]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout_s,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if proc.returncode != 0:
            log.warning("tts_worker exit=%s stderr=%s", proc.returncode, proc.stderr.decode(errors="ignore"))
            return False
        return True
    except subprocess.TimeoutExpired:
        log.error("tts_worker TIMEOUT after %.1fs", timeout_s)
        return False
    except Exception as ex:
        log.exception("tts_worker failed: %s", ex)
        return False

def beep_fallback():
    try:
        import winsound
        try: winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception: winsound.Beep(880, 160)
    except Exception:
        pass
