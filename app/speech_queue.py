# app/speech_queue.py
import time
import threading
import queue
import logging
from typing import Optional, Callable

logger = logging.getLogger("app.speech")

class SpeakQueue:
    """
    Continuous speech queue with periodic repeat functionality.
    
    Features:
    - Speaks new sentences immediately (respects min_gap_secs)
    - Repeats same sentence every repeat_same_after_secs if no changes
    - Current sentence tracking for continuous operation
    - Gate control for conditional speech enabling
    """
    
    def __init__(self, speech, min_gap_secs=0.7, repeat_same_after_secs=3.0, gate: Optional[Callable[[], bool]]=None):
        self.speech = speech
        self.min_gap = float(min_gap_secs)
        self.repeat_same = float(repeat_same_after_secs)
        self.q = queue.Queue()
        self.last_text = None
        self.last_ts = 0.0
        self._run = False
        self._th = None
        self._current_hint = None  # last "current sentence" hint from vision loop
        self._enabled = True  # Enable/disable flag
        self._gate = gate  # callable returning bool
        self._started = False  # Track if thread has been started
        
        # Gate control Events
        self._speech_enabled = threading.Event()
        self._camera_running = threading.Event()
        self._speech_enabled.set()  # Start enabled
        self._camera_running.clear()  # Start with camera off

    def start(self):
        """Start the speech worker thread"""
        if self._run: 
            return
        self._run = True
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()
        logger.info("Speech worker thread started")

    def stop(self):
        """Stop the speech worker thread"""
        self._run = False
        try:
            self.q.put_nowait("")
        except Exception:
            pass

    def set_speech_enabled(self, enabled: bool):
        """Enable or disable speech output"""
        if enabled:
            self._speech_enabled.set()
        else:
            self._speech_enabled.clear()
            
    def set_camera_running(self, running: bool):
        """Set camera running state"""
        if running:
            self._camera_running.set()
        else:
            self._camera_running.clear()
            
    def pause(self, *, clear=True, stop_playback=True):
        """Pause speech with optional queue clearing and playback stopping"""
        self._speech_enabled.clear()
        if clear:
            try:
                while True:
                    self.q.get_nowait()
            except Exception:
                pass
        if stop_playback:
            try:
                self.speech.stop_playback()
            except Exception:
                pass
                
    def resume(self):
        """Resume speech output"""
        self._speech_enabled.set()

    def is_alive(self) -> bool:
        """Check if the worker thread is alive"""
        return bool(self._th and self._th.is_alive())

    def hint_current_sentence(self, text):
        """
        Called every frame (or often) with the latest sentence; enables periodic repeats
        """
        self._current_hint = text

    def enqueue(self, text):
        """
        Always try to enqueue; worker enforces pacing/duplicates
        """
        try:
            self.q.put_nowait(text or "")
        except Exception:
            pass

    def _should_speak_now(self, text, now):
        """Determine if we should speak the text now based on timing rules"""
        if not text:
            return False
        
        # If this is exactly what we spoke last, check minimum gap
        if text == self.last_text and (now - self.last_ts) < self.min_gap:
            return False
        
        # Always speak if it's different text
        if text != self.last_text:
            return True
        
        # For same text, only speak after repeat interval
        return (now - self.last_ts) >= self.repeat_same

    def _loop(self):
        """Main speech worker loop with final gate checks"""
        while self._run:
            try:
                # Try to get new text from queue
                try:
                    text = self.q.get(timeout=0.3)
                except queue.Empty:
                    # No new items; consider repeating the current sentence
                    text = self._current_hint or ""
                
                now = time.time()
                
                # Check if we should speak this text now
                if not self._should_speak_now(text, now):
                    continue
                
                # CRITICAL: Final gate check before speaking
                if not (self._speech_enabled.is_set() and self._camera_running.is_set()):
                    continue  # Gates closed: drop text and continue
                
                # Attempt to speak only if gates are open
                ok = self.speech.speak_vi(text)
                if ok:
                    self.last_text = text
                    self.last_ts = now
                    
            except Exception as e:
                logger.exception("Speak worker error: %s", e)
                time.sleep(0.1)
