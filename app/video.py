# app/video.py
import cv2
import threading
import time
import logging
import inspect
from typing import Optional, Tuple

logger = logging.getLogger("app.video")

_BACKENDS = {
    "AUTO": 0,
    "DSHOW": getattr(cv2, "CAP_DSHOW", 700),   # Windows DirectShow
    "MSMF":  getattr(cv2, "CAP_MSMF", 1400),   # Windows Media Foundation
}

_FOURCCS = [
    ("MJPG", cv2.VideoWriter_fourcc(*"MJPG")),
    ("YUY2", cv2.VideoWriter_fourcc(*"YUY2")),
    ("NONE", None),
]

class CameraReader:
    def __init__(self, index: int = 0, width: int = 640, height: int = 480, fps: int = 30,
                 prefer_backend: str = "DSHOW", prefer_fourcc: str = "MJPG",
                 warmup_secs: float = 3.0):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.prefer_backend = prefer_backend.upper() if prefer_backend else "AUTO"
        self.prefer_fourcc = prefer_fourcc.upper() if prefer_fourcc else "MJPG"
        self.warmup_secs = warmup_secs

        self.cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.latest_frame = None
        self.backend_used = None
        self.fourcc_used = None
        self.last_error = None

    def _try_open(self, backend_name: str, fourcc_name: str) -> bool:
        """Try to open camera with specific backend and fourcc combination."""
        api = _BACKENDS.get(backend_name, 0)
        fourcc_val = next((v for n, v in _FOURCCS if n == fourcc_name), None)

        cap = cv2.VideoCapture(self.index, api)
        if not cap.isOpened():
            try:
                cap.release()
            except:
                pass
            return False

        # Set properties
        if fourcc_val is not None:
            cap.set(cv2.CAP_PROP_FOURCC, fourcc_val)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except:
            pass
        try:
            cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
        except:
            pass

        # Warmup read - test if frames actually arrive
        t0 = time.time()
        ok_frames = 0
        while time.time() - t0 < self.warmup_secs:
            ok, frame = cap.read()
            if ok and frame is not None:
                ok_frames += 1
                if ok_frames >= 3:
                    self.cap = cap
                    self.backend_used = backend_name
                    self.fourcc_used = fourcc_name
                    return True
            time.sleep(0.02)

        # No frames: release and fail
        cap.release()
        return False

    def start(self) -> bool:
        """Start camera with backend and fourcc fallback. Returns True if successful."""
        if self._running:
            logger.info("Camera already running")
            return True

        self.last_error = None
        
        # Build preference order
        backends = [self.prefer_backend] + [b for b in ["DSHOW", "MSMF", "AUTO"] if b != self.prefer_backend]
        fourccs = [self.prefer_fourcc] + [n for n, _ in _FOURCCS if n != self.prefer_fourcc]

        opened = False
        reasons = []
        for b in backends:
            for f in fourccs:
                ok = self._try_open(b, f)
                logger.info("Open try backend=%s fourcc=%s -> %s", b, f, ok)
                if ok:
                    opened = True
                    break
                else:
                    reasons.append(f"{b}/{f}")
            if opened:
                break

        if not opened:
            self.last_error = f"Failed to open idx={self.index} with any combo: {', '.join(reasons)}"
            logger.error(self.last_error)
            return False

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Camera thread started (backend=%s fourcc=%s)", self.backend_used, self.fourcc_used)
        return True

    def _loop(self):
        """Camera read loop with failure monitoring."""
        fail = 0
        while self._running and self.cap and self.cap.isOpened():
            ok, frame = self.cap.read()
            if not ok or frame is None:
                fail += 1
                if fail >= 150:
                    self.last_error = f"Consecutive read failures on {self.backend_used}/{self.fourcc_used}"
                    logger.error(self.last_error)
                    break
                time.sleep(0.02)
                continue
            
            fail = 0
            with self._lock:
                self.latest_frame = frame
        
        self._running = False
        try:
            if self.cap:
                self.cap.release()
        finally:
            self.cap = None
        logger.info("Camera thread exited")

    def read(self):
        """Get latest frame copy."""
        with self._lock:
            return None if self.latest_frame is None else self.latest_frame.copy()

    def stop(self, *, _allow=False):
        """Stop camera with authorization check."""
        caller = inspect.stack()[1]
        logger.info("Camera.stop() called by %s:%s", caller.filename, caller.lineno)
        
        if not _allow:
            # Only allow through our guarded wrapper
            logger.warning("Camera.stop() blocked (unauthorized caller)")
            return
            
        if not self._running:
            return
            
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        self.cap = None
        logger.info("Camera stopped (authorized)")

    @property
    def running(self) -> bool:
        return self._running

    def status(self) -> str:
        return f"running={self._running}, backend={self.backend_used}, fourcc={self.fourcc_used}, last_error={self.last_error}"
