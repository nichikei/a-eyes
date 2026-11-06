"""End-to-end tests for the FastAPI backend with a stub detector.

The stub stands in for YOLO so these run in a second, without model weights,
a GPU or a Windows voice.
"""

import base64
import threading
import time

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import app.detector
import simple_yolo_backend as backend


class StubDetector:
    """Returns a fixed set of detections in Detector.detect()'s format."""

    is_loaded = True

    def __init__(self, *args, **kwargs):
        self.calls = 0

    def detect(self, frame):
        self.calls += 1
        h, w = frame.shape[:2]
        return [
            # Large person dead centre.
            {"label": "person", "confidence": 0.91, "bbox": [w * 0.4, h * 0.1, w * 0.6, h * 0.95]},
            # Traffic light on the far left.
            {"label": "traffic light", "confidence": 0.62, "bbox": [5, 5, 60, 120]},
            # Below the per-class confidence floor -> dropped.
            {"label": "dog", "confidence": 0.10, "bbox": [400, 300, 500, 400]},
            # Smaller than MIN_AREA_RATIO -> dropped as noise.
            {"label": "cup", "confidence": 0.90, "bbox": [600, 400, 603, 403]},
        ]


def _frame_b64(w=640, h=480):
    img = np.full((h, w, 3), 127, dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app.detector, "Detector", StubDetector)
    spoken = []
    monkeypatch.setattr(backend, "_speak_caption", spoken.append)
    monkeypatch.setattr(backend, "_last_spoken_text", None)
    with TestClient(backend.app) as c:
        c.spoken = spoken
        yield c


def test_health_reports_ready_detector(client):
    body = client.get("/health").json()
    assert body["status"] == "healthy"
    assert body["detector_loaded"] is True


def test_describe_filters_and_describes_in_vietnamese(client):
    r = client.post("/api/describe", json={"image": _frame_b64(), "autoSpeak": False})
    assert r.status_code == 200
    body = r.json()

    assert body["objects"] == ["person", "traffic light"]
    assert body["count"] == 2
    person, light = body["objects_detail"]
    assert person["vi"] == "người"
    assert person["clock"].startswith("12 giờ")
    assert light["vi"] == "đèn giao thông"
    assert light["clock"].startswith("10 giờ")
    assert "người" in body["caption_fast"]
    assert set(body["timings_ms"]) == {"decode", "detect", "caption"}


def test_describe_rejects_garbage_image(client):
    r = client.post("/api/describe", json={"image": "not-an-image", "autoSpeak": False})
    assert r.status_code == 400


def test_auto_speak_queues_caption_once(client):
    for _ in range(3):
        client.post("/api/describe", json={"image": _frame_b64(), "autoSpeak": True})
    backend._tts_executor.submit(lambda: None).result(timeout=5)  # drain queue
    # Same scene three times -> spoken once (dedupe).
    assert len(client.spoken) == 1
    assert "người" in client.spoken[0]


def test_response_does_not_wait_for_speech(client, monkeypatch):
    done = threading.Event()

    def slow_tts(text):
        time.sleep(1.5)
        done.set()

    monkeypatch.setattr(backend, "_speak_caption", slow_tts)
    t0 = time.perf_counter()
    r = client.post("/api/describe", json={"image": _frame_b64(), "autoSpeak": True})
    elapsed = time.perf_counter() - t0
    assert r.status_code == 200
    # Regression: speech used to run inline, adding its full duration here.
    assert elapsed < 1.0
    assert done.wait(timeout=5)


def test_empty_scene(client, monkeypatch):
    monkeypatch.setattr(StubDetector, "detect", lambda self, frame: [])
    body = client.post("/api/describe", json={"image": _frame_b64(), "autoSpeak": False}).json()
    assert body["count"] == 0
    assert body["confidence"] == 0.0
    assert body["caption_fast"].startswith("Khung hình trống")
