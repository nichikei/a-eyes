"""
Enhanced Detection System - Hệ thống nhận diện nâng cao
Tối ưu hóa độ chính xác và giảm thiểu lỗi nhận diện sai
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import time
import logging
from collections import deque, Counter
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)

@dataclass
class DetectionHistory:
    """Lưu trữ lịch sử nhận diện để validation"""
    label: str
    confidence: float
    bbox: List[float]
    timestamp: float
    frame_id: int

class EnhancedDetectionValidator:
    """
    Validator nâng cao để giảm thiểu lỗi nhận diện
    - Multi-frame validation
    - Temporal consistency
    - Confidence trending
    - Spatial stability
    """
    
    def __init__(self, 
                 history_frames: int = 5,
                 min_consecutive_frames: int = 2,
                 confidence_threshold_boost: float = 0.05,
                 spatial_tolerance: float = 0.3):
        self.history_frames = history_frames
        self.min_consecutive_frames = min_consecutive_frames
        self.confidence_threshold_boost = confidence_threshold_boost
        self.spatial_tolerance = spatial_tolerance
        
        # Lịch sử nhận diện theo thời gian
        self.detection_history: deque = deque(maxlen=history_frames)
        self.frame_counter = 0
        
        # Lock để thread-safe
        self.lock = threading.Lock()
        
        logger.info(f"✅ Enhanced detection validator initialized: "
                   f"history={history_frames}, min_frames={min_consecutive_frames}")
    
    def validate_detections(self, raw_detections: List[Dict]) -> List[Dict]:
        """
        Validate detections using multiple criteria
        """
        with self.lock:
            self.frame_counter += 1
            current_time = time.time()
            
            # Store current detections
            current_detections = []
            for det in raw_detections:
                current_detections.append(DetectionHistory(
                    label=det["label"],
                    confidence=det.get("confidence", det.get("conf", 0.0)),
                    bbox=det.get("bbox", [0, 0, 0, 0]),
                    timestamp=current_time,
                    frame_id=self.frame_counter
                ))
            
            self.detection_history.append(current_detections)
            
            # Apply validation rules
            validated_detections = []
            for det in current_detections:
                if self._is_detection_valid(det):
                    # Boost confidence for consistently detected objects
                    boosted_conf = self._calculate_boosted_confidence(det)
                    
                    validated_det = {
                        "label": det.label,
                        "confidence": boosted_conf,
                        "bbox": det.bbox,
                        "validation_score": self._calculate_validation_score(det)
                    }
                    validated_detections.append(validated_det)
            
            return validated_detections
    
    def _is_detection_valid(self, detection: DetectionHistory) -> bool:
        """
        Check if detection is valid based on historical consistency
        """
        if len(self.detection_history) < self.min_consecutive_frames:
            # Not enough history, accept high-confidence detections
            return detection.confidence > 0.4
        
        # Count consecutive appearances
        consecutive_count = self._count_consecutive_appearances(detection)
        
        # Check spatial stability
        spatial_stability = self._check_spatial_stability(detection)
        
        # Validation rules
        rules = [
            # Rule 1: High confidence detections are generally accepted
            detection.confidence > 0.6,
            
            # Rule 2: Medium confidence with temporal consistency
            (detection.confidence > 0.3 and consecutive_count >= self.min_consecutive_frames),
            
            # Rule 3: Spatially stable detections
            (detection.confidence > 0.25 and spatial_stability > 0.7),
            
            # Rule 4: Common objects with lower threshold
            (detection.label in ["person", "car", "chair", "table"] and 
             detection.confidence > 0.2 and consecutive_count >= 2)
        ]
        
        return any(rules)
    
    def _count_consecutive_appearances(self, detection: DetectionHistory) -> int:
        """
        Count how many consecutive frames this object appeared in
        """
        count = 0
        for frame_detections in reversed(self.detection_history):
            found = False
            for hist_det in frame_detections:
                if (hist_det.label == detection.label and 
                    self._calculate_bbox_overlap(detection.bbox, hist_det.bbox) > 0.5):
                    found = True
                    break
            
            if found:
                count += 1
            else:
                break
        
        return count
    
    def _check_spatial_stability(self, detection: DetectionHistory) -> float:
        """
        Check how stable the object position is across frames
        """
        if len(self.detection_history) < 2:
            return 1.0
        
        overlaps = []
        for frame_detections in reversed(list(self.detection_history)[:-1]):  # Exclude current frame
            best_overlap = 0.0
            for hist_det in frame_detections:
                if hist_det.label == detection.label:
                    overlap = self._calculate_bbox_overlap(detection.bbox, hist_det.bbox)
                    best_overlap = max(best_overlap, overlap)
            overlaps.append(best_overlap)
        
        return np.mean(overlaps) if overlaps else 0.0
    
    def _calculate_boosted_confidence(self, detection: DetectionHistory) -> float:
        """
        Boost confidence for consistently detected objects
        """
        base_confidence = detection.confidence
        consecutive_count = self._count_consecutive_appearances(detection)
        spatial_stability = self._check_spatial_stability(detection)
        
        # Boost factors
        temporal_boost = min(consecutive_count * 0.05, 0.2)  # Max 0.2 boost
        stability_boost = spatial_stability * 0.1  # Max 0.1 boost
        
        boosted = base_confidence + temporal_boost + stability_boost
        return min(boosted, 1.0)  # Cap at 1.0
    
    def _calculate_validation_score(self, detection: DetectionHistory) -> float:
        """
        Calculate overall validation score (0-1)
        """
        consecutive_count = self._count_consecutive_appearances(detection)
        spatial_stability = self._check_spatial_stability(detection)
        
        # Normalize factors
        temporal_score = min(consecutive_count / self.history_frames, 1.0)
        confidence_score = detection.confidence
        stability_score = spatial_stability
        
        # Weighted combination
        validation_score = (
            0.4 * confidence_score +
            0.3 * temporal_score +
            0.3 * stability_score
        )
        
        return validation_score
    
    def _calculate_bbox_overlap(self, bbox1: List[float], bbox2: List[float]) -> float:
        """
        Calculate IoU (Intersection over Union) between two bounding boxes
        """
        try:
            x1_1, y1_1, x2_1, y2_1 = bbox1[:4]
            x1_2, y1_2, x2_2, y2_2 = bbox2[:4]
            
            # Calculate intersection
            x1_i = max(x1_1, x1_2)
            y1_i = max(y1_1, y1_2)
            x2_i = min(x2_1, x2_2)
            y2_i = min(y2_1, y2_2)
            
            if x2_i <= x1_i or y2_i <= y1_i:
                return 0.0
            
            intersection = (x2_i - x1_i) * (y2_i - y1_i)
            
            # Calculate union
            area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
            area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
            union = area1 + area2 - intersection
            
            return intersection / union if union > 0 else 0.0
        except:
            return 0.0

class ImagePreprocessor:
    """
    Cải thiện chất lượng ảnh trước khi nhận diện
    """
    
    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        """
        Cải thiện chất lượng ảnh để tăng độ chính xác nhận diện
        """
        enhanced = image.copy()
        
        # 1. Cải thiện độ sáng và contrast
        enhanced = ImagePreprocessor._auto_brightness_contrast(enhanced)
        
        # 2. Giảm noise
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # 3. Sharpening nhẹ
        enhanced = ImagePreprocessor._unsharp_mask(enhanced)
        
        return enhanced
    
    @staticmethod
    def _auto_brightness_contrast(image: np.ndarray, clip_hist_percent: float = 1.0) -> np.ndarray:
        """
        Tự động điều chỉnh brightness và contrast
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate grayscale histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_size = len(hist)
        
        # Calculate cumulative distribution from the histogram
        accumulator = []
        accumulator.append(float(hist[0]))
        for index in range(1, hist_size):
            accumulator.append(accumulator[index -1] + float(hist[index]))
        
        # Locate points to clip
        maximum = accumulator[-1]
        clip_hist_percent *= (maximum / 100.0)
        clip_hist_percent /= 2.0
        
        # Locate left cut
        minimum_gray = 0
        while accumulator[minimum_gray] < clip_hist_percent:
            minimum_gray += 1
        
        # Locate right cut
        maximum_gray = hist_size - 1
        while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
            maximum_gray -= 1
        
        # Calculate alpha and beta values
        alpha = 255 / (maximum_gray - minimum_gray)
        beta = -minimum_gray * alpha
        
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    
    @staticmethod
    def _unsharp_mask(image: np.ndarray, kernel_size: Tuple[int, int] = (5, 5), 
                      sigma: float = 1.0, amount: float = 1.0, threshold: int = 0) -> np.ndarray:
        """
        Unsharp mask để làm sắc nét ảnh
        """
        blurred = cv2.GaussianBlur(image, kernel_size, sigma)
        sharpened = float(amount + 1) * image - float(amount) * blurred
        sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
        sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
        sharpened = sharpened.round().astype(np.uint8)
        
        if threshold > 0:
            low_contrast_mask = np.absolute(image - blurred) < threshold
            np.copyto(sharpened, image, where=low_contrast_mask)
        
        return sharpened

class ConfidenceOptimizer:
    """
    Tối ưu hóa confidence threshold động dựa trên context
    """
    
    def __init__(self):
        self.base_thresholds = {
            "person": 0.15,
            "car": 0.25,
            "truck": 0.30,
            "bus": 0.35,
            "motorcycle": 0.20,
            "bicycle": 0.25,
            "chair": 0.30,
            "table": 0.35,
            "sofa": 0.40,
            "bed": 0.45,
            "tv": 0.35,
            "laptop": 0.40,
            "mouse": 0.45,
            "keyboard": 0.40,
            "cell phone": 0.35,
            "book": 0.40,
            "clock": 0.45,
            "bottle": 0.30,
            "cup": 0.35,
            "bowl": 0.40,
            "banana": 0.35,
            "apple": 0.30,
            "sandwich": 0.40,
            "pizza": 0.35,
            "donut": 0.45,
            "cake": 0.40,
            "potted plant": 0.35,
            "cat": 0.45,
            "dog": 0.40,
            "horse": 0.50,
            "sheep": 0.45,
            "cow": 0.45,
            "elephant": 0.60,
            "bear": 0.65,
            "zebra": 0.55,
            "giraffe": 0.60,
        }
        
        self.default_threshold = 0.25
        
        # Context-based adjustments
        self.brightness_factor = 1.0
        self.contrast_factor = 1.0
        
    def get_optimized_threshold(self, label: str, image_stats: Optional[Dict] = None) -> float:
        """
        Get optimized confidence threshold for a specific label and context
        """
        base_threshold = self.base_thresholds.get(label, self.default_threshold)
        
        if image_stats is None:
            return base_threshold
        
        # Adjust based on image quality
        brightness = image_stats.get("brightness", 127)
        contrast = image_stats.get("contrast", 50)
        
        # Lower threshold for poor lighting conditions
        if brightness < 80 or brightness > 200:
            base_threshold *= 0.9
        
        # Lower threshold for low contrast images
        if contrast < 30:
            base_threshold *= 0.85
        
        # Higher threshold for very noisy images
        edge_density = image_stats.get("edge_density", 0.1)
        if edge_density > 0.3:
            base_threshold *= 1.1
        
        return max(0.1, min(0.8, base_threshold))  # Clamp between 0.1 and 0.8

# Global instances
enhanced_validator = EnhancedDetectionValidator()
confidence_optimizer = ConfidenceOptimizer()

def process_enhanced_detection(raw_detections: List[Dict], image: np.ndarray = None) -> List[Dict]:
    """
    Main function to process detections with enhanced validation
    """
    try:
        # 1. Preprocess image if provided
        if image is not None:
            enhanced_image = ImagePreprocessor.enhance_image(image)
            image_stats = analyze_image_quality(enhanced_image)
        else:
            image_stats = None
        
        # 2. Optimize confidence thresholds
        optimized_detections = []
        for det in raw_detections:
            label = det["label"]
            confidence = det.get("confidence", det.get("conf", 0.0))
            
            # Get optimized threshold
            threshold = confidence_optimizer.get_optimized_threshold(label, image_stats)
            
            # Apply threshold
            if confidence >= threshold:
                optimized_detections.append(det)
        
        # 3. Apply multi-frame validation
        validated_detections = enhanced_validator.validate_detections(optimized_detections)
        
        # 4. Sort by validation score
        validated_detections.sort(key=lambda x: x.get("validation_score", 0), reverse=True)
        
        logger.info(f"🔍 Enhanced detection: {len(raw_detections)} → {len(optimized_detections)} → {len(validated_detections)}")
        
        return validated_detections
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced detection: {e}")
        return raw_detections  # Fallback to original detections

def analyze_image_quality(image: np.ndarray) -> Dict:
    """
    Analyze image quality metrics
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    return {
        "brightness": np.mean(gray),
        "contrast": np.std(gray),
        "edge_density": np.sum(cv2.Canny(gray, 50, 150) > 0) / gray.size,
        "sharpness": cv2.Laplacian(gray, cv2.CV_64F).var()
    }