"""
detector.py
Object Detection Module for AI Eyes Vision Assistant (clean & robust)

- Ultralytics YOLO (v5/v8 weights đều OK) với warmup
- Bilingual labels (EN + VI) có fallback mapping nội bộ
- Ngưỡng conf/IoU/imgsz cấu hình qua env
- Lọc box nhiễu theo diện tích tối thiểu (min_area_ratio)
- Thống kê hiệu năng (fps, avg latency)
- API ổn định: Detector.detect() trả list dict {label_en,label_vi,label,class_name,confidence,bbox}
"""

from __future__ import annotations

import os
import time
import logging
from typing import List, Dict, Any, Optional

import numpy as np
import cv2

try:
    from ultralytics import YOLO  # supports v5/v8 weights
except Exception:
    YOLO = None

logger = logging.getLogger(__name__)


# --------- Vietnamese fallback mapping (dùng khi không có vi_nlp) ----------
_COCO_VI_FALLBACK = {
    'person': 'người', 'bicycle': 'xe đạp', 'car': 'ô tô', 'motorcycle': 'xe máy',
    'airplane': 'máy bay', 'bus': 'xe buýt', 'train': 'tàu hỏa', 'truck': 'xe tải',
    'boat': 'thuyền', 'traffic light': 'đèn giao thông', 'fire hydrant': 'vòi cứu hỏa',
    'stop sign': 'biển dừng', 'parking meter': 'đồng hồ đỗ xe', 'bench': 'ghế dài',
    'bird': 'chim', 'cat': 'mèo', 'dog': 'chó', 'horse': 'ngựa', 'sheep': 'cừu',
    'cow': 'bò', 'elephant': 'voi', 'bear': 'gấu', 'zebra': 'ngựa vằn', 'giraffe': 'hươu cao cổ',
    'backpack': 'ba lô', 'umbrella': 'ô', 'handbag': 'túi xách', 'tie': 'cà vạt', 'suitcase': 'vali',
    'frisbee': 'đĩa bay', 'skis': 'ván trượt tuyết', 'snowboard': 'ván trượt tuyết',
    'sports ball': 'bóng', 'kite': 'diều', 'baseball bat': 'gậy bóng chày',
    'baseball glove': 'găng bóng chày', 'skateboard': 'ván trượt', 'surfboard': 'ván lướt',
    'tennis racket': 'vợt tennis', 'bottle': 'chai', 'wine glass': 'ly rượu', 'cup': 'cốc',
    'fork': 'nĩa', 'knife': 'dao', 'spoon': 'thìa', 'bowl': 'bát', 'banana': 'chuối',
    'apple': 'táo', 'sandwich': 'bánh sandwich', 'orange': 'cam', 'broccoli': 'bông cải xanh',
    'carrot': 'cà rốt', 'hot dog': 'xúc xích', 'pizza': 'pizza', 'donut': 'bánh donut',
    'cake': 'bánh ngọt', 'chair': 'ghế', 'couch': 'ghế sofa', 'potted plant': 'chậu cây',
    'bed': 'giường', 'dining table': 'bàn ăn', 'toilet': 'bồn cầu', 'tv': 'tivi',
    'laptop': 'laptop', 'mouse': 'chuột', 'remote': 'điều khiển', 'keyboard': 'bàn phím',
    'cell phone': 'điện thoại', 'microwave': 'lò vi sóng', 'oven': 'lò nướng',
    'toaster': 'máy nướng bánh', 'sink': 'bồn rửa', 'refrigerator': 'tủ lạnh',
    'book': 'sách', 'clock': 'đồng hồ', 'vase': 'bình hoa', 'scissors': 'kéo',
    'teddy bear': 'gấu bông', 'hair drier': 'máy sấy tóc', 'toothbrush': 'bàn chải đánh răng'
}


def _vi_label(en: str) -> str:
    # Thử import mapping “xịn”, nếu không có thì dùng fallback
    try:
        from .vi_nlp import COCO_VI  # type: ignore
        return COCO_VI.get(en, _COCO_VI_FALLBACK.get(en, en))
    except Exception:
        return _COCO_VI_FALLBACK.get(en, en)


class _Perf:
    """Nhẹ nhàng lưu thông số hiệu năng (EMA)."""
    def __init__(self, alpha: float = 0.2):
        self.alpha = alpha
        self.ema_infer = None  # ms
        self.total_frames = 0
        self._t_last = None
        self._ema_fps = None

    def update_infer_ms(self, ms: float):
        self.total_frames += 1
        if self.ema_infer is None:
            self.ema_infer = ms
        else:
            self.ema_infer = self.alpha * ms + (1 - self.alpha) * self.ema_infer

    def tick_fps(self):
        now = time.time()
        if self._t_last is not None:
            dt = now - self._t_last
            if dt > 0:
                fps = 1.0 / dt
                if self._ema_fps is None:
                    self._ema_fps = fps
                else:
                    self._ema_fps = self.alpha * fps + (1 - self.alpha) * self._ema_fps
        self._t_last = now

    def stats(self) -> Dict[str, float]:
        return {
            "avg_inference_ms": float(self.ema_infer or 0.0),
            "fps": float(self._ema_fps or 0.0),
            "total_frames": int(self.total_frames),
        }


class Detector:
    """
    YOLO-based object detector for AI Eyes.
    Trả về detection theo định dạng thống nhất cho backend.
    """

    def __init__(
        self,
        model_path: str = "yolov5s.pt",
        device: str = "cpu",
        default_conf: Optional[float] = None,
        default_iou: Optional[float] = None,
        imgsz: Optional[int] = None,
        min_area_ratio: Optional[float] = None,
    ):
        """
        Args:
            model_path: đường dẫn .pt (v5/v8 đều OK)
            device: "cpu" | "cuda"
            default_conf: ngưỡng conf mặc định (env YOLO_CONF nếu None)
            default_iou: ngưỡng IoU NMS (env YOLO_IOU nếu None)
            imgsz: kích thước suy luận (env YOLO_IMGSZ nếu None)
            min_area_ratio: lọc box quá nhỏ theo tỉ lệ ảnh (env YOLO_MIN_AREA_RATIO nếu None)
        """
        self.model_path = model_path
        self.device = device

        self.default_conf = (
            float(os.getenv("YOLO_CONF", "0.10")) if default_conf is None else default_conf
        )
        self.default_iou = (
            float(os.getenv("YOLO_IOU", "0.45")) if default_iou is None else default_iou
        )
        self.imgsz = int(os.getenv("YOLO_IMGSZ", "640")) if imgsz is None else int(imgsz)
        self.min_area_ratio = (
            float(os.getenv("YOLO_MIN_AREA_RATIO", "0.0"))
            if min_area_ratio is None
            else float(min_area_ratio)
        )

        self.model = None
        self.is_loaded = False
        self.names = {}
        self.perf = _Perf()

        self.load_model()

    # ---------------------- Model load & warmup ----------------------
    def load_model(self) -> bool:
        if YOLO is None:
            logger.error("Ultralytics not available. Install: pip install ultralytics")
            self.is_loaded = False
            return False
        try:
            logger.info(f"Loading YOLO model: {self.model_path}")
            self.model = YOLO(self.model_path)

            # Move device (for v5/v8 under the hood)
            try:
                if hasattr(self.model, "to"):
                    self.model.to(self.device)  # some versions expose .to
                elif hasattr(self.model, "model") and hasattr(self.model.model, "to"):
                    self.model.model.to(self.device)
                logger.info(f"Model moved to device: {self.device}")
            except Exception as e:
                logger.warning(f"Move to device failed (will use default): {e}")

            # Half precision cho CUDA
            if self.device == "cuda":
                try:
                    if hasattr(self.model, "model"):
                        self.model.model.half()
                        logger.info("Using half precision (CUDA)")
                except Exception as e:
                    logger.warning(f"Half precision failed: {e}")

            # Lấy mapping class -> name
            try:
                if hasattr(self.model, "names"):
                    self.names = self.model.names
                else:
                    self.names = {}
            except Exception:
                self.names = {}

            # Warmup
            dummy = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
            _ = self.model(dummy, conf=self.default_conf, iou=self.default_iou, imgsz=self.imgsz, verbose=False)
            self.is_loaded = True
            logger.info("YOLO model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            self.is_loaded = False
            return False

    # ---------------------- Detection ----------------------
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Args:
            frame (BGR np.ndarray)
        Returns:
            List[dict]: each detection has:
                - label (legacy EN), label_en, label_vi, class_name (legacy EN)
                - confidence (float)
                - bbox [x1,y1,x2,y2] (int)
                - class_id (int)
        """
        if not self.is_loaded or self.model is None:
            logger.warning("Model not loaded. Reloading...")
            if not self.load_model():
                return []

        H, W = frame.shape[:2]
        t0 = time.time()

        try:
            results = self.model(
                frame,
                conf=self.default_conf,
                iou=self.default_iou,
                imgsz=self.imgsz,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"YOLO inference error: {e}")
            return []

        dets: List[Dict[str, Any]] = []
        try:
            # Ultralytics API: results is list (1 image)
            r = results[0]
            boxes = getattr(r, "boxes", None)
            if boxes is None or len(boxes) == 0:
                self._update_perf(t0)
                return dets

            xyxy = boxes.xyxy.cpu().numpy() if hasattr(boxes, "xyxy") else None
            confs = boxes.conf.cpu().numpy() if hasattr(boxes, "conf") else None
            clses = boxes.cls.cpu().numpy() if hasattr(boxes, "cls") else None

            if xyxy is None or confs is None or clses is None:
                self._update_perf(t0)
                return dets

            # name map: prefer model.names, else result.names
            name_map = self.names or getattr(r, "names", {}) or {}

            for i in range(len(boxes)):
                x1, y1, x2, y2 = xyxy[i].tolist()
                conf = float(confs[i])
                cls_id = int(clses[i])
                label_en = str(name_map.get(cls_id, f"class_{cls_id}"))

                # Lọc theo diện tích tối thiểu (nếu bật)
                if self.min_area_ratio > 0.0:
                    box_w = max(1.0, x2 - x1)
                    box_h = max(1.0, y2 - y1)
                    area_ratio = (box_w * box_h) / float(W * H)
                    if area_ratio < self.min_area_ratio:
                        continue

                label_vi = _vi_label(label_en)

                dets.append({
                    "class_id": cls_id,
                    "label_en": label_en,
                    "label_vi": label_vi,
                    "confidence": conf,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    # legacy fields:
                    "label": label_en,
                    "class_name": label_en,
                })
        except Exception as e:
            logger.error(f"Detection parse error: {e}")
            dets = []

        self._update_perf(t0)
        return dets

    def _update_perf(self, t0: float):
        infer_ms = (time.time() - t0) * 1000.0
        self.perf.update_infer_ms(infer_ms)
        self.perf.tick_fps()

    # ---------------------- Visualization ----------------------
    def draw_boxes(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        img = frame.copy()
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            conf = float(d.get("confidence", 0.0))
            label = d.get("label", "obj")

            # color theo độ tin cậy
            if conf >= 0.7:
                color = (0, 200, 0)
            elif conf >= 0.5:
                color = (0, 165, 255)
            else:
                color = (0, 0, 255)

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            text = f"{label} {conf:.2f}"
            (tw, th), bl = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (x1, y1 - th - bl - 4), (x1 + tw + 2, y1), color, -1)
            cv2.putText(img, text, (x1 + 1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return img

    # ---------------------- Convenience / compatibility ----------------------
    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """Alias cho draw_boxes để tương thích code cũ."""
        return self.draw_boxes(frame, detections)

    def get_performance_stats(self) -> Dict[str, float]:
        """Trả các thống kê hiệu năng: avg_inference_ms, fps, total_frames."""
        return self.perf.stats()


# --------- Backward-compat wrapper (giữ tối thiểu) ----------
class ObjectDetector(Detector):
    """
    Tương thích code cũ:
    - confidence_threshold: vẫn chấp nhận nhưng ưu tiên dùng YOLO_CONF/YOLO_IOU
    - language: giữ để không gãy, nhưng Detector đã trả sẵn EN/VI
    """

    def __init__(self, model_name: str = "yolov5s", confidence_threshold: float = 0.5, language: str = "vi", **kwargs):
        model_path = f"{model_name}.pt"
        super().__init__(model_path=model_path, **kwargs)
        self.confidence_threshold = float(confidence_threshold)
        self.language = language

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        dets = super().detect(frame)
        # Lọc thêm theo confidence_threshold nếu muốn tương thích
        return [d for d in dets if d.get("confidence", 0.0) >= self.confidence_threshold]
