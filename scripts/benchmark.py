"""Measure A-Eyes latency on this machine.

Runs the real /api/describe pipeline in-process (base64 JPEG decode -> YOLO ->
filtering -> Vietnamese caption) on 1280x720 JPEG frames, the size and quality
the web client sends, and reports per-stage latency percentiles.

    python scripts/benchmark.py              # 50 frames per image, CPU
    python scripts/benchmark.py --runs 200 --json bench_results.json

Speech is disabled (autoSpeak=False): it runs on a background thread and is
not part of the request latency.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import cv2  # noqa: E402
import numpy as np  # noqa: E402


def pct(values, p):
    values = sorted(values)
    k = (len(values) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def summarize(values):
    return {
        "mean": round(statistics.fmean(values), 1),
        "p50": round(pct(values, 50), 1),
        "p95": round(pct(values, 95), 1),
        "min": round(min(values), 1),
    }


def load_frames(width, height):
    """Ultralytics' bundled sample photos, resized to the client's frame size."""
    from ultralytics.utils import ASSETS

    frames = {}
    for name in ("bus.jpg", "zidane.jpg"):
        img = cv2.imread(str(Path(ASSETS) / name))
        # Centre-crop to the target aspect ratio, then resize (no stretching).
        h, w = img.shape[:2]
        target = width / height
        if w / h > target:
            nw = int(h * target); x0 = (w - nw) // 2; img = img[:, x0:x0 + nw]
        else:
            nh = int(w / target); y0 = (h - nh) // 2; img = img[y0:y0 + nh]
        frames[name] = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
    return frames


def to_data_url(img, quality=80):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    assert ok
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def cpu_name():
    if platform.system() == "Windows":
        try:
            import subprocess

            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
            if out:
                return out
        except Exception:
            pass
    return platform.processor() or platform.machine()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=50, help="frames per sample image")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--json", help="write results to this file")
    ap.add_argument("--model", help="weights or exported model dir (sets YOLO_MODEL)")
    ap.add_argument("--auto-speak", action="store_true",
                    help="benchmark the fast path the web client's continuous mode uses (skips enhanced filtering)")
    args = ap.parse_args()

    os.environ.setdefault("CAPTION_DEVICE", "cpu")
    if args.model:
        os.environ["YOLO_MODEL"] = args.model
    import torch
    import simple_yolo_backend as backend

    t0 = time.perf_counter()
    asyncio.run(backend.startup_event())
    startup_s = time.perf_counter() - t0
    if not (backend.detector and backend.detector.is_loaded):
        sys.exit("YOLO detector failed to load; see log above")

    frames = load_frames(args.width, args.height)
    results = {}
    for name, img in frames.items():
        payload = to_data_url(img)
        req = backend.DescribeRequest(image=payload, autoSpeak=args.auto_speak)
        backend._speak_caption = lambda text: None  # never actually speak
        backend.describe(req)  # warm caches for this resolution

        stages = {"decode": [], "detect": [], "caption": [], "total": []}
        objects = None
        for _ in range(args.runs):
            t = time.perf_counter()
            resp = backend.describe(req)
            stages["total"].append((time.perf_counter() - t) * 1000)
            for k in ("decode", "detect", "caption"):
                stages[k].append(resp.timings_ms[k])
            objects = resp.objects
        results[name] = {
            "objects": objects,
            "caption_text": resp.caption_fast,
            **{k: summarize(v) for k, v in stages.items()},
        }

    # Fallback path (no YOLO): HSV + Canny heuristics only.
    from smart_fallback import smart_fallback_detection

    img = next(iter(frames.values()))
    fb = []
    for _ in range(args.runs):
        t = time.perf_counter()
        smart_fallback_detection(img)
        fb.append((time.perf_counter() - t) * 1000)

    all_totals = [v for r in results.values() for v in [r["total"]["p50"]]]
    report = {
        "machine": {
            "cpu": cpu_name(),
            "threads": os.cpu_count(),
            "device": backend.selected_device,
            "python": platform.python_version(),
            "torch": torch.__version__,
        },
        "model": os.path.basename(getattr(backend.detector, "model_path", "?")),
        "imgsz": backend.detector.imgsz,
        "frame": f"{args.width}x{args.height} JPEG q80",
        "runs_per_image": args.runs,
        "startup_s": round(startup_s, 2),
        "images": results,
        "fallback_ms": summarize(fb),
        "pipeline_p50_ms": round(statistics.fmean(all_totals), 1),
        "pipeline_fps_p50": round(1000 / statistics.fmean(all_totals), 1),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
