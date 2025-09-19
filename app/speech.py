# app/speech.py
# Clean, robust Vietnamese TTS with queue + Windows SAPI OneCore (Microsoft An)
from __future__ import annotations
import os
import time
import threading
import queue
import logging
import tempfile
from typing import Optional, Callable, Tuple

# ---- Env defaults (only used if gTTS/pygame fallback) ----
os.environ.setdefault("SDL_AUDIODRIVER", "wasapi")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

logger = logging.getLogger("app.speech")
logger.setLevel(logging.INFO)

# =========================
# Config loader (optional)
# =========================
def _load_config_safe() -> dict:
    try:
        from .config_loader import load_config
        d = load_config() or {}
        if not isinstance(d, dict): d = {}
        return d
    except Exception:
        return {}

# =========================
# Helpers
# =========================
def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None: return default
    return v.strip() not in ("0", "false", "False", "")

# =========================
# Engine 1: Windows SAPI (OneCore) — Ưu tiên Microsoft An
# =========================
class SapiEngine:
    """Windows SAPI, chọn giọng OneCore (Microsoft An) nếu có. Blocking speak."""
    def __init__(self, voice_name_hint: str = "microsoft an", voice_lang_hint: str = "vi",
                 volume: int = 100, rate: int = 0):
        self.voice_name_hint = (voice_name_hint or "microsoft an").lower()
        self.voice_lang_hint = (voice_lang_hint or "vi").lower()
        self.volume = int(_env_float("TTS_VOLUME", volume))
        self.rate   = int(_env_float("TTS_RATE", rate))
        self._last_desc = None

    def _select_vi_voice(self, sp) -> Tuple[bool, Optional[str]]:
        import comtypes.client

        def pick_onecore_by_name(hive: str):
            try:
                cat = comtypes.client.CreateObject("SAPI.SpObjectTokenCategory")
                if hive == "HKCU":
                    cat.SetId(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Speech_OneCore\Voices")
                else:
                    cat.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices")
                toks = cat.EnumerateTokens()
                for i in range(toks.Count):
                    t = toks.Item(i)
                    d = t.GetDescription()
                    if self.voice_name_hint in d.lower():
                        return t, d
            except Exception:
                pass
            return None, None

        def pick_onecore_by_lang(hive: str):
            try:
                cat = comtypes.client.CreateObject("SAPI.SpObjectTokenCategory")
                if hive == "HKCU":
                    cat.SetId(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Speech_OneCore\Voices")
                else:
                    cat.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices")
                toks = cat.EnumerateTokens()
                for i in range(toks.Count):
                    t = toks.Item(i)
                    d = t.GetDescription().lower()
                    if ("viet" in d) or ("vi-vn" in d) or (self.voice_lang_hint in d):
                        return t, t.GetDescription()
            except Exception:
                pass
            return None, None

        # 1) OneCore by exact name (HKCU -> HKLM)
        for hive in ("HKCU", "HKLM"):
            tok, desc = pick_onecore_by_name(hive)
            if tok:
                try:
                    sp.Voice = tok
                    logger.info(f"[TTS] OneCore selected ({hive}): {desc}")
                    return True, desc
                except Exception as e:
                    logger.warning(f"[TTS] OneCore set failed ({hive}): {e}")

        # 2) OneCore by language
        for hive in ("HKCU", "HKLM"):
            tok, desc = pick_onecore_by_lang(hive)
            if tok:
                try:
                    sp.Voice = tok
                    logger.info(f"[TTS] OneCore selected by lang ({hive}): {desc}")
                    return True, desc
                except Exception as e:
                    logger.warning(f"[TTS] OneCore set failed ({hive}): {e}")

        # 3) Desktop SAPI by 'vi' hint (hiếm khi có)
        try:
            toks = sp.GetVoices()
            for i in range(toks.Count):
                d = toks.Item(i).GetDescription().lower()
                if "viet" in d or "vi-vn" in d or self.voice_lang_hint in d:
                    sp.Voice = toks.Item(i)
                    logger.info(f"[TTS] Desktop selected by hint: {d}")
                    return True, d
        except Exception:
            pass

        # 4) Fallback to first desktop voice (English) — không mong muốn
        try:
            toks = sp.GetVoices()
            if toks.Count > 0:
                d = toks.Item(0).GetDescription()
                sp.Voice = toks.Item(0)
                logger.info(f"[TTS] Fallback desktop voice: {d}")
                return True, d
        except Exception:
            pass

        return False, None

    def speak_vi(self, text: str) -> bool:
        if not text: return False
        try:
            import comtypes, comtypes.client
            comtypes.CoInitialize()
            try:
                sp = comtypes.client.CreateObject("SAPI.SpVoice")
                sp.Volume = max(0, min(100, self.volume))
                sp.Rate   = max(-10, min(10, self.rate))
                ok, desc = self._select_vi_voice(sp)
                self._last_desc = desc or "unknown"
                # Blocking speak
                sp.Speak(text)
                return True
            finally:
                try: comtypes.CoUninitialize()
                except Exception: pass
        except Exception as e:
            logger.error(f"[TTS] SAPI speak failed: {e}")
            return False

    def stop_playback(self):
        # With blocking speak(), nothing async to stop here.
        pass

# =========================
# Engine 2: pyttsx3 (offline) — fallback
# =========================
class PyttsxEngine:
    def __init__(self, lang_hint="vi", volume=1.0, rate=190):
        self.lang_hint = (lang_hint or "vi").lower()
        self.volume = float(volume)
        self.rate = int(rate)

    def speak_vi(self, text: str) -> bool:
        if not text: return False
        try:
            import pyttsx3
            eng = pyttsx3.init()
            # pick vi voice if any
            for v in eng.getProperty('voices'):
                if 'vi' in v.id.lower() or 'vietnamese' in getattr(v, "name", "").lower():
                    eng.setProperty('voice', v.id)
                    break
            eng.setProperty('rate', self.rate)
            eng.setProperty('volume', max(0.0, min(1.0, self.volume)))
            eng.say(text)
            eng.runAndWait()
            eng.stop()
            return True
        except Exception as e:
            logger.error(f"[TTS] pyttsx3 failed: {e}")
            return False

    def stop_playback(self):
        pass

# =========================
# Engine 3: gTTS + pygame (online) — fallback
# =========================
class GttsEngine:
    def __init__(self, lang="vi", volume=1.0):
        self.lang = lang
        self.volume = float(volume)

    def _ensure_mixer(self) -> bool:
        try:
            import pygame
            if pygame.mixer.get_init() is None:
                try:
                    pygame.mixer.init(frequency=22050, channels=1, buffer=1024)
                    logger.info(f"Pygame mixer initialized | driver={os.getenv('SDL_AUDIODRIVER')}")
                except Exception as e:
                    # fallback DirectSound
                    os.environ["SDL_AUDIODRIVER"] = "directsound"
                    import pygame as _pg
                    _pg.mixer.init(frequency=22050, channels=1, buffer=1024)
                    logger.info("Pygame mixer initialized with fallback | driver=directsound")
            import pygame as _pg
            _pg.mixer.music.set_volume(max(0.0, min(1.0, self.volume)))
            return True
        except Exception as e:
            logger.error(f"Failed to init pygame mixer: {e}")
            return False

    def speak_vi(self, text: str) -> bool:
        if not text: return False
        try:
            from gtts import gTTS
            import pygame
            if not self._ensure_mixer():
                return False

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                path = f.name
            try:
                gTTS(text=text, lang=self.lang, slow=False).save(path)
            except Exception as e:
                logger.error(f"gTTS generate failed: {e}")
                try: os.unlink(path)
                except Exception: pass
                return False

            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
            finally:
                try: os.unlink(path)
                except Exception: pass
            return True
        except Exception as e:
            logger.error(f"[TTS] gTTS playback failed: {e}")
            return False

    def stop_playback(self):
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

# =========================
# Speech facade (choose engine)
# =========================
class Speech:
    """
    Simple facade: choose engine by ENV/config.
    Methods needed by the rest of the app:
      - speak_vi(text) -> bool
      - stop_playback()
    """
    def __init__(self):
        cfg = _load_config_safe().get("speech", {})
        # ENV has highest priority
        engine_name = (os.getenv("TTS_ENGINE") or cfg.get("engine") or "sapi").lower()
        lang_hint   = os.getenv("TTS_VOICE_LANG", cfg.get("lang_hint", "vi"))
        name_hint   = os.getenv("TTS_VOICE_NAME", cfg.get("name_hint", "microsoft an"))

        vol_num = _env_float("TTS_VOLUME", cfg.get("volume", 1.0))
        rate_num = _env_float("TTS_RATE", cfg.get("rate", 0))

        if engine_name in ("sapi", "auto"):
            self.engine = SapiEngine(voice_name_hint=name_hint, voice_lang_hint=lang_hint,
                                     volume=int(vol_num * 100), rate=int(rate_num))
            self.fallback = PyttsxEngine(lang_hint=lang_hint, volume=vol_num)
        elif engine_name == "pyttsx3":
            self.engine = PyttsxEngine(lang_hint=lang_hint, volume=vol_num)
            self.fallback = None
        else:  # "gtts"
            self.engine = GttsEngine(lang="vi", volume=vol_num)
            self.fallback = None

        logger.info(f"[TTS] Engine selected: {self.engine.__class__.__name__}")

    def speak_vi(self, text: str) -> bool:
        ok = self.engine.speak_vi(text)
        if not ok and self.fallback:
            logger.info("[TTS] primary failed, falling back...")
            ok = self.fallback.speak_vi(text)
        return ok

    def stop_playback(self):
        try:
            self.engine.stop_playback()
        except Exception:
            pass
        try:
            if self.fallback:
                self.fallback.stop_playback()
        except Exception:
            pass

# =========================
# SpeakQueue (threaded, dedupe, throttle, gates, session-cancel)
# =========================
class SpeakQueue:
    """
    Queue-based speaker:
      - min_interval_ms: tối thiểu giữa 2 lần nói
      - dedupe_window_ms: bỏ qua câu trùng trong cửa sổ thời gian
      - gate: callable() -> bool để bật/tắt nói
      - session-cancel: hủy ngay các câu còn trong queue
    """
    def __init__(self, speech_enabled_evt: threading.Event = None,
                 cam_running_evt: threading.Event = None,
                 speech: Speech | None = None,
                 min_gap_secs=0.7, repeat_same_after_secs=3.0,
                 min_interval_ms=1200, dedupe_window_ms=2500,
                 gate: Optional[Callable[[], bool]] = None):
        cfg = _load_config_safe().get("speech", {})
        self.min_interval_ms = float(cfg.get('min_interval_ms', min_interval_ms))
        self.dedupe_window_ms = float(cfg.get('dedupe_window_ms', dedupe_window_ms))
        self.min_gap = float(min_gap_secs)
        self.repeat_same = float(repeat_same_after_secs)

        self.speech = speech or Speech()
        self.q: queue.Queue = queue.Queue()
        self._run = True
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()

        self._speech_enabled = speech_enabled_evt or threading.Event()
        self._camera_running = cam_running_evt or threading.Event()
        self._speech_enabled.set()
        self._camera_running.clear()
        self._gate = gate

        self._session = 0
        self._lock = threading.Lock()

        self.last_text = None
        self.last_ts = 0.0
        self._last_spoken_ts_ms = 0.0
        self._history: list[tuple[float, str]] = []  # (ts_sec, text)
        self._current_hint = ""

        logger.info("Speech worker thread started")

    # ----- gates / controls -----
    def set_cam_running(self, on: bool): 
        (self._camera_running.set() if on else self._camera_running.clear())
        logger.info(f"Camera running: {on}")

    def set_speech_enabled(self, on: bool):
        (self._speech_enabled.set() if on else self._speech_enabled.clear())
        logger.info(f"Speech enabled: {on}")

    def cam_is_on(self) -> bool: return self._camera_running.is_set()
    def speech_is_on(self) -> bool: return self._speech_enabled.is_set()

    def emergency_mute(self):
        self.pause(clear=True, stop_playback=True)
        logger.info("Emergency mute activated")

    # ----- session / cancel -----
    def _bump_session(self):
        with self._lock:
            self._session += 1

    def _get_session(self) -> int:
        with self._lock:
            return self._session

    # ----- public queue API -----
    def hint_current_sentence(self, text: str):
        self._current_hint = text or ""

    def enqueue(self, text: str) -> bool:
        if not text: return False
        if not (self._speech_enabled.is_set() and self._camera_running.is_set()):
            return False
        sid = self._get_session()
        try:
            self.q.put_nowait((sid, text))
            return True
        except Exception:
            return False

    def pause(self, *, clear=True, stop_playback=True):
        self._bump_session()
        self._speech_enabled.clear()
        self._camera_running.clear()
        if clear:
            try:
                while True: self.q.get_nowait()
            except Exception: pass
        if stop_playback:
            try: self.speech.stop_playback()
            except Exception: pass

    def pause_and_clear(self):  # alias
        self.pause(clear=True, stop_playback=True)

    def resume(self):
        self._speech_enabled.set()

    def stop(self):
        self._run = False
        try: self.q.put_nowait(("", ""))  # wake up thread
        except Exception: pass
        try: self.speech.stop_playback()
        except Exception: pass

    # ----- internals -----
    def _is_duplicate(self, text: str, now_sec: float) -> bool:
        cutoff = now_sec - (self.dedupe_window_ms / 1000.0)
        self._history = [(ts, t) for ts, t in self._history if ts > cutoff]
        for ts, t in self._history:
            if t == text:
                return True
        return False

    def _should_speak_now(self, text: str, now_sec: float) -> bool:
        if not text: return False
        if self._gate and not self._gate(): return False
        if not (self._speech_enabled.is_set() and self._camera_running.is_set()):
            return False

        # global min interval in ms
        if self._last_spoken_ts_ms > 0:
            if (time.time() * 1000 - self._last_spoken_ts_ms) < self.min_interval_ms:
                return False

        if self._is_duplicate(text, now_sec):
            return False

        # same as last? enforce min gap or repeat interval
        if text == (self.last_text or ""):
            if (now_sec - self.last_ts) < self.min_gap:
                return False
            return (now_sec - self.last_ts) >= self.repeat_same

        return True

    def _speak_once(self, text: str) -> bool:
        ok = self.speech.speak_vi(text)
        if ok:
            now_ms = time.time() * 1000
            self._last_spoken_ts_ms = now_ms
            self._history.append((now_ms / 1000.0, text))
        return ok

    def _loop(self):
        while self._run:
            try:
                try:
                    sid, text = self.q.get(timeout=0.3)
                except queue.Empty:
                    sid = self._get_session()
                    text = self._current_hint or ""

                # session/gates check
                if sid != self._get_session(): 
                    continue
                if not (self._speech_enabled.is_set() and self._camera_running.is_set()):
                    continue

                now = time.time()
                if not self._should_speak_now(text, now):
                    continue

                # final check before speak
                if sid != self._get_session():
                    continue
                if not (self._speech_enabled.is_set() and self._camera_running.is_set()):
                    continue

                if self._speak_once(text):
                    self.last_text = text
                    self.last_ts = now

            except Exception as e:
                logger.exception(f"Speak worker error: {e}")
                time.sleep(0.1)
