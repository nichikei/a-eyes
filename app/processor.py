"""
Vision Processor Module for AI Eyes Vision Assistant

This module serves as the central coordinator that integrates all AI components:
object detection, color recognition, distance estimation, OCR, and speech synthesis.
It processes camera frames and generates natural Vietnamese descriptions for blind users.
"""

import cv2
import numpy as np
import time
import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple, Union
import threading
import queue
from dataclasses import dataclass
from enum import Enum

# Import AI Eyes modules
from .detector import ObjectDetector, Detector
from .color_recognition import ColorRecognizer
from .distance_estimation import DistanceEstimator
from .ocr import VietnameseOCR
from .speech import Speech  # SAPI OneCore facade (ưu tiên Microsoft An)
from .vi_nlp import map_label_en_to_vi, COCO_VI

# Create reverse mapping VI→EN
VI_EN = {vi: en for en, vi in COCO_VI.items()}

# Global error rate limiting for TTS spam prevention
_last_error_tts = 0.0
_ERROR_COOLDOWN = 6.0  # seconds

# Module logger
log = logging.getLogger("app.processor")

def _normalize_det(d: dict) -> dict:
    """
    Normalize detection dictionary to ensure all required fields exist.
    
    Args:
        d: Detection dictionary with potential missing fields
        
    Returns:
        Normalized detection with guaranteed label_en, label_vi, and other fields
    """
    # Prefer explicit fields, fallback to legacy/unknown keys
    en = d.get("label_en") or d.get("class_name") or d.get("label") or d.get("name")
    vi = d.get("label_vi") or map_label_en_to_vi(en)
    
    # Normalize core fields
    d["label_en"] = en or "object"
    d["label_vi"] = vi
    
    # Normalize optional fields with Vietnamese fallbacks
    d["color_vi"] = d.get("color_vi") or d.get("color") or "không rõ"
    d["distance_vi"] = d.get("distance_vi") or d.get("distance") or "trung bình"
    d["position_vi"] = d.get("position_vi") or d.get("position") or "ở giữa"
    
    return d


class RegionType(Enum):
    """Frame regions for spatial descriptions."""
    FRONT = "front"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"
    FULL = "full"


@dataclass
class ProcessingResult:
    """Container for processing results."""
    frame: np.ndarray
    detections: List[Dict[str, Any]]
    text_regions: List[Dict[str, Any]]
    description: str
    processing_time: float
    region_processed: RegionType


class VisionProcessor:
    """
    Central vision processing system that coordinates all AI components.
    
    Features:
    - Multi-modal AI processing (vision, OCR, speech)
    - Natural Vietnamese sentence generation
    - Region-specific processing for directional commands
    - Real-time performance optimization
    - Intelligent description prioritization
    - Configurable processing modes
    """
    
    def __init__(self,
                 confidence_threshold: float = 0.5,
                 language: str = 'vi',
                 max_detections: int = 10,
                 enable_speech: bool = True,
                 enable_threading: bool = True,
                 external_speech_queue=None):
        """
        Initialize vision processor.
        
        Args:
            confidence_threshold: Minimum confidence for detections
            language: Language for descriptions ('vi' for Vietnamese)
            max_detections: Maximum objects to describe
            enable_speech: Enable automatic speech output
            enable_threading: Enable background processing
            external_speech_queue: External speech queue to use instead of internal one
        """
        self.confidence_threshold = confidence_threshold
        self.language = language
        self.max_detections = max_detections
        self.enable_speech = enable_speech
        self.enable_threading = enable_threading
        self.external_speech_queue = external_speech_queue
        
        # Initialize AI components
        self.detector = Detector(model_path="yolov5s.pt")
        self.color_recognizer = ColorRecognizer(language=language)
        self.distance_estimator = DistanceEstimator(language=language)
        self.ocr = VietnameseOCR()
        
        # Speech synthesizer (optional)
        self.speech = None
        if enable_speech:
            try:
                self.speech = Speech()  # tự chọn Microsoft An (OneCore) nếu có
                logging.info("Speech engine ready (SAPI/OneCore)")
            except Exception as e:
                logging.warning(f"Speech engine not available: {e}")
        
        # Processing state
        self.last_description = ""
        self.last_processing_time = 0
        self.frame_count = 0
        self.processing_times = []
        
        # Region definitions for spatial processing
        self.region_definitions = self._initialize_regions()
        
        # Vietnamese sentence templates
        self.sentence_templates = self._initialize_sentence_templates()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Threading for non-blocking speech
        self.speech_queue = queue.Queue() if enable_threading else None
        self.speech_thread = None
        if enable_threading:
            self._start_speech_worker()
        
        self.logger.info("VisionProcessor initialized successfully")
    
    def _initialize_regions(self) -> Dict[RegionType, Tuple[float, float, float, float]]:
        """Initialize frame region definitions (relative coordinates 0-1)."""
        return {
            RegionType.FRONT: (0.2, 0.2, 0.8, 0.8),      # Center 60%
            RegionType.LEFT: (0.0, 0.0, 0.4, 1.0),       # Left 40%
            RegionType.RIGHT: (0.6, 0.0, 1.0, 1.0),      # Right 40%
            RegionType.TOP: (0.0, 0.0, 1.0, 0.4),        # Top 40%
            RegionType.BOTTOM: (0.0, 0.6, 1.0, 1.0),     # Bottom 40%
            RegionType.CENTER: (0.25, 0.25, 0.75, 0.75), # Center 50%
            RegionType.FULL: (0.0, 0.0, 1.0, 1.0)        # Entire frame
        }
    
    def _initialize_sentence_templates(self) -> Dict[str, List[str]]:
        """Initialize Vietnamese sentence templates for natural descriptions."""
        return {
            'single_object': [
                "{position} có một {object} {color}, {distance}.",
                "Tôi thấy một {object} {color} {position}, {distance}.",
                "Có một {object} {color} {position}, cách {distance}."
            ],
            
            'multiple_objects': [
                "{position} có {count} vật thể: {objects}.",
                "Tôi phát hiện {count} thứ {position}: {objects}.",
                "Có {count} vật thể {position}: {objects}."
            ],
            
            'object_with_text': [
                "{position} có một {object} {color} với chữ '{text}', {distance}.",
                "Tôi thấy một {object} {color} ghi '{text}' {position}, {distance}."
            ],
            
            'text_only': [
                "{position} có chữ viết: '{text}'.",
                "Tôi đọc được: '{text}' {position}.",
                "Có văn bản: '{text}' {position}."
            ],
            
            'no_detection': [
                "{position} không có gì đặc biệt.",
                "Tôi không thấy gì {position}.",
                "{position} trống."
            ],
            
            'distance_alert': [
                "Cảnh báo: {object} rất gần, chỉ cách {distance}!",
                "Chú ý: {object} ở ngay trước mặt!"
            ]
        }
    
    def _start_speech_worker(self):
        """Start background thread for speech processing."""
        if not self.enable_threading:
            return
        
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        self.logger.info("Speech worker thread started")
    
    def _speech_worker(self):
        """Background worker for speech processing."""
        while True:
            try:
                speech_request = self.speech_queue.get(timeout=1.0)
                if speech_request is None:  # Shutdown signal
                    break
                
                text, priority = speech_request
                if self.speech:
                    self.speech.speak_vi(text)
                
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Speech worker error: {e}")
    
    def process_frame_realtime(self, frame: np.ndarray, region: RegionType = RegionType.FULL) -> tuple:
        """
        Process frame for real-time loop, returning (annotated_frame, sentence_or_none).
        Does not call TTS directly - caller should enqueue sentences.
        """
        try:
            start_time = time.time()
            
            # Get region coordinates
            roi_coords = self._get_region_coordinates(frame, region)
            
            # Extract ROI
            x1, y1, x2, y2 = roi_coords
            roi = frame[y1:y2, x1:x2]
            
            # Detect objects in ROI
            detections = self.detector.detect(roi)
            
            # Normalize detections to ensure all required fields exist
            norm_dets = [_normalize_det(d) for d in detections]
            
            # Debug log first few normalized detections (once per run)
            if not getattr(self, "_logged_norm_once", False):
                for i, d in enumerate(norm_dets[:3]):
                    log.info("norm_det[%d]: en=%s vi=%s conf=%.2f", i, d.get("label_en"), d.get("label_vi"), d.get("conf", -1))
                self._logged_norm_once = True
            
            # Adjust detection coordinates to full frame
            for detection in norm_dets:
                if 'bbox' in detection:
                    bbox = detection['bbox']
                    detection['bbox'] = [
                        bbox[0] + x1, bbox[1] + y1,
                        bbox[2] + x1, bbox[3] + y1
                    ]
            
            # Process detections
            enhanced_detections = self._enhance_detections(frame, norm_dets)
            
            # Build description
            description = None
            if enhanced_detections:
                description = self._generate_description(
                    enhanced_detections,
                    [],  # No text regions in this context
                    region,
                    force_description=False
                )
                
                # Only return description if it's new or significantly different
                if description and description != self.last_description:
                    self.last_description = description
                else:
                    description = None  # Suppress duplicate
            elif not enhanced_detections:
                # Fallback sentence when no detections
                description = "Chưa thấy vật thể rõ ràng."
            
            # Draw annotations
            annotated_frame = self._draw_annotations(
                frame, 
                enhanced_detections, 
                [], 
                roi_coords
            )
            
            return annotated_frame, description
            
        except Exception as e:
            log.error("Description generation error: %s", e, exc_info=True)
            
            # Rate-limited error TTS
            global _last_error_tts
            now = time.time()
            if now - _last_error_tts > _ERROR_COOLDOWN:
                _last_error_tts = now
                # Return a single short Vietnamese error sentence (once per cooldown)
                return frame, "Có lỗi khi mô tả cảnh vật."
            else:
                # Suppress TTS; still show overlay/log
                return frame, None

    def process_frame(self,
                     frame: np.ndarray,
                     region: RegionType = RegionType.FULL,
                     enable_ocr: bool = True,
                     enable_speech: bool = None,
                     force_description: bool = False) -> ProcessingResult:
        """
        Process a frame with full AI pipeline.
        
        Args:
            frame: Input frame from camera
            region: Region to focus processing on
            enable_ocr: Enable text recognition
            enable_speech: Override speech setting
            force_description: Force generation of description
            
        Returns:
            ProcessingResult with annotated frame and description
        """
        start_time = time.time()
        
        try:
            # Validate frame
            if frame is None or frame.size == 0:
                return self._create_empty_result(frame, region)
            
            # Get region of interest
            roi_coords = self._get_region_coordinates(frame, region)
            
            # Run object detection (already enhanced with color, distance, position)
            detections = self._process_detections(frame, roi_coords)
            
            # Run OCR if enabled
            text_regions = []
            if enable_ocr:
                text_regions = self._process_text_recognition(frame, roi_coords)
            
            # Generate natural Vietnamese description with enhanced detections
            description = self._generate_description(
                detections, 
                text_regions, 
                region,
                force_description
            )
            
            # Draw annotations on frame
            annotated_frame = self._draw_annotations(
                frame, 
                detections, 
                text_regions, 
                roi_coords
            )
            
            # Handle speech output - send sentence to speech.speak() if enabled
            if enable_speech is None:
                enable_speech = self.enable_speech
            
            if enable_speech and description and description != self.last_description:
                # CRITICAL: Validate Vietnamese sentence before speech
                from .vi_nlp import validate_vietnamese_sentence
                is_valid, english_tokens = validate_vietnamese_sentence(description)
                if not is_valid:
                    self.logger.error("CRITICAL: English tokens found: %s | Sentence: %s", english_tokens, description)
                    # Auto-fix common English words
                    description = description.replace("a ", "").replace("person", "người")
                    # Re-validate after auto-fix
                    is_valid_after_fix, remaining_tokens = validate_vietnamese_sentence(description)
                    if not is_valid_after_fix:
                        self.logger.warning("Auto-fix incomplete, remaining tokens: %s", remaining_tokens)
                        # Create a fallback Vietnamese sentence
                        description = "Có vật thể được phát hiện."
                
                # Use external speech queue if available, otherwise fall back to internal
                if self.external_speech_queue:
                    self.external_speech_queue.enqueue(description)
                elif self.speech:
                    self.speech.speak_vi(description)
                self.last_description = description
            
            # Track performance
            processing_time = time.time() - start_time
            self._update_performance_stats(processing_time)
            
            return ProcessingResult(
                frame=annotated_frame,
                detections=detections,
                text_regions=text_regions,
                description=description,
                processing_time=processing_time,
                region_processed=region
            )
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {e}")
            return self._create_error_result(frame, region, str(e))
    
    def _get_region_coordinates(self, frame: np.ndarray, region: RegionType) -> Tuple[int, int, int, int]:
        """Convert relative region coordinates to absolute pixel coordinates."""
        h, w = frame.shape[:2]
        rel_x1, rel_y1, rel_x2, rel_y2 = self.region_definitions[region]
        
        x1 = int(rel_x1 * w)
        y1 = int(rel_y1 * h)
        x2 = int(rel_x2 * w)
        y2 = int(rel_y2 * h)
        
        return (x1, y1, x2, y2)
    
    def _process_detections(self, frame: np.ndarray, roi_coords: Tuple[int, int, int, int]) -> List[Dict[str, Any]]:
        """Process object detections in specified region with enhanced pipeline."""
        try:
            # Run YOLOv5 detection on full frame
            yolo_detections = self.detector.detect(frame)
            
            # Filter detections that fall within ROI and process each one
            x1_roi, y1_roi, x2_roi, y2_roi = roi_coords
            enhanced_detections = []
            
            for detection in yolo_detections:
                # Apply confidence threshold
                if detection['confidence'] < self.confidence_threshold:
                    continue
                
                bbox = detection['bbox']
                x1, y1, x2, y2 = bbox
                
                # Check if detection center is within ROI
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                if not (x1_roi <= center_x <= x2_roi and y1_roi <= center_y <= y2_roi):
                    continue
                
                # Import Vietnamese mapping
                from .vi_nlp import map_label_en_to_vi, map_color_en_to_vi, map_distance_en_to_vi
                
                # Get Vietnamese label - CRITICAL: Use Vietnamese only
                label_vi = detection.get('label_vi')
                if not label_vi:
                    # Fallback: translate from English
                    label_en = detection.get('label_en', detection.get('label', 'object'))
                    label_vi = map_label_en_to_vi(label_en)
                    self.logger.warning(f"Detection missing label_vi, translated {label_en} → {label_vi}")
                
                # Always use Vietnamese label for sentences
                label = label_vi
                
                # Get dominant color
                try:
                    color_info = self.color_recognizer.get_dominant_color(frame, bbox)
                    color_vi = color_info.get('vietnamese_name', 'không xác định') if isinstance(color_info, dict) else str(color_info)
                except Exception as e:
                    self.logger.warning(f"Color recognition error: {e}")
                    color_vi = "không xác định"
                
                # Estimate distance
                try:
                    distance_info = self.distance_estimator.estimate_distance(bbox, frame.shape[0])
                    if isinstance(distance_info, dict):
                        distance_vi = distance_info.get('vietnamese_description', 'khoảng cách trung bình')
                    else:
                        distance_vi = str(distance_info)
                except Exception as e:
                    self.logger.warning(f"Distance estimation error: {e}")
                    distance_vi = "khoảng cách trung bình"
                
                # Determine position (left/center/right)
                frame_width = frame.shape[1]
                if center_x < frame_width * 0.33:
                    position_vi = "bên trái"
                elif center_x > frame_width * 0.67:
                    position_vi = "bên phải"
                else:
                    position_vi = "ở giữa"
                
                # Create enhanced detection
                enhanced_detection = {
                    'label': label,
                    'label_vi': label_vi,  # CRITICAL: Ensure Vietnamese label is available
                    'confidence': detection['confidence'],
                    'bbox': bbox,
                    'center': (int(center_x), int(center_y)),
                    'color_vi': color_vi,
                    'distance_vi': distance_vi,
                    'position_vi': position_vi,
                    'class_name': label,  # For backward compatibility
                    'color': color_vi,    # For backward compatibility
                    'distance_text': distance_vi,  # For backward compatibility
                    'spatial_position': position_vi  # For backward compatibility
                }
                
                enhanced_detections.append(enhanced_detection)
            
            # Sort by confidence and limit
            enhanced_detections.sort(key=lambda x: x['confidence'], reverse=True)
            return enhanced_detections[:self.max_detections]
            
        except Exception as e:
            self.logger.error(f"Detection processing error: {e}")
            return []
    
    def _process_text_recognition(self, frame: np.ndarray, roi_coords: Tuple[int, int, int, int]) -> List[Dict[str, Any]]:
        """Process text recognition in specified region."""
        try:
            # Extract ROI for OCR
            x1, y1, x2, y2 = roi_coords
            roi = frame[y1:y2, x1:x2]
            
            if roi.size == 0:
                return []
            
            # Detect text regions
            text_regions = self.ocr.detect_text_regions(roi)
            
            # Adjust coordinates to full frame
            for region in text_regions:
                bbox = region['bbox']
                region['bbox'] = (
                    bbox[0] + x1,
                    bbox[1] + y1,
                    bbox[2] + x1,
                    bbox[3] + y1
                )
            
            return text_regions
            
        except Exception as e:
            self.logger.error(f"OCR processing error: {e}")
            return []
    
    def _enhance_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance detections with color and distance information."""
        enhanced = []
        
        for detection in detections:
            try:
                bbox = detection['bbox']
                
                # Get label from normalized detection (prefer Vietnamese)
                label_vi = detection.get('label_vi', 'vật thể')
                label_en = detection.get('label_en', 'object')
                
                # Add color information
                color = self.color_recognizer.get_dominant_color(frame, bbox)
                detection['color'] = color
                
                # Add Vietnamese color description
                detection['color_vi'] = self.color_recognizer.get_color_vi(color)
                
                # Add distance information
                distance_info = self.distance_estimator.get_distance_description(
                    bbox, 
                    frame.shape[0], 
                    label_en,  # Use English for internal calculations
                    include_metric=True
                )
                detection.update(distance_info)
                
                # Add Vietnamese distance description
                detection['distance_vi'] = self.distance_estimator.get_distance_vi(distance_info.get('distance_meters', 0))
                
                # Add spatial position
                detection['spatial_position'] = self._get_spatial_position(bbox, frame.shape)
                
                # Ensure backward compatibility
                detection['class_name'] = label_en
                
                enhanced.append(detection)
                
            except Exception as e:
                self.logger.error(f"Detection enhancement error: {e}")
                enhanced.append(detection)  # Add original detection
        
        return enhanced
    
    def _get_spatial_position(self, bbox: Tuple[int, int, int, int], frame_shape: Tuple[int, int]) -> str:
        """Determine spatial position description for an object."""
        x1, y1, x2, y2 = bbox
        h, w = frame_shape[:2]
        
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Horizontal position
        if center_x < w * 0.33:
            horizontal = "bên trái" if self.language == 'vi' else "on the left"
        elif center_x > w * 0.67:
            horizontal = "bên phải" if self.language == 'vi' else "on the right"
        else:
            horizontal = "ở giữa" if self.language == 'vi' else "in the center"
        
        # Vertical position
        if center_y < h * 0.33:
            vertical = "phía trên" if self.language == 'vi' else "at the top"
        elif center_y > h * 0.67:
            vertical = "phía dưới" if self.language == 'vi' else "at the bottom"
        else:
            vertical = ""
        
        # Combine positions
        if vertical:
            return f"{horizontal}, {vertical}" if self.language == 'vi' else f"{horizontal}, {vertical}"
        else:
            return horizontal
    
    def _generate_description(self,
                            detections: List[Dict[str, Any]],
                            text_regions: List[Dict[str, Any]],
                            region: RegionType,
                            force_description: bool = False) -> str:
        """Generate natural Vietnamese description of the scene using enhanced detection data."""
        try:
            if not detections:
                if force_description:
                    return "Không phát hiện được vật thể nào."
                return ""
            
            # Generate description for each detection using Vietnamese labels only
            descriptions = []
            
            # Helper function to safely extract labels
            def _safe_labels(det: dict):
                """Extract labels with safe fallbacks, never treat 'người' as missing"""
                
                label_en = (det.get("label_en") or det.get("class_name") or "").strip().lower()
                label_vi = (det.get("label_vi") or det.get("class_name_vi") or "").strip().lower()

                # If "label_en" accidentally contains Vietnamese → map back to EN
                if label_en not in COCO_VI:
                    if label_en in VI_EN:
                        label_en = VI_EN[label_en]

                # Complete label_vi
                if not label_vi or label_vi == label_en or label_vi not in VI_EN:
                    label_vi = COCO_VI.get(label_en, "vật thể")

                return label_en, label_vi
            
            for detection in detections:
                # Import Vietnamese mapping functions and new classifier
                from .vi_nlp import map_color_en_to_vi, map_distance_en_to_vi, map_spatial_en_to_vi
                from .vi_nlp import vi_classifier, normalize_vi_sentence
                
                # Use safe label extraction 
                label_en, label_vi = _safe_labels(detection)
                
                # Only warn if truly missing after safe extraction (not for valid Vietnamese like "người")
                if label_vi == "vật thể" and label_en != "object":
                    self.logger.warning("Fallback VI label used | en=%s", label_en)
                
                # Get color in Vietnamese with safe fallback
                color_vi = detection.get('color_vi') or detection.get('color') or "không rõ"
                
                # Get distance in Vietnamese with safe fallback
                distance_vi = detection.get('distance_vi') or detection.get('distance') or "trung bình"
                
                # Get spatial position in Vietnamese with safe fallback
                position_vi = detection.get('position_vi') or detection.get('position') or "ở giữa"
                
                # Use new classifier system to get correct noun phrase
                np = vi_classifier(label_en, label_vi)
                
                # Log noun phrase for QA (optional debugging)
                self.logger.debug("NP=%s | en=%s vi=%s", np, label_en, label_vi)
                
                # Build sentence with correct classifier
                sentence = f"{np} màu {color_vi} ở khoảng cách {distance_vi}, {position_vi}"
                
                # Apply new normalizer to fix spatial issues and ensure proper formatting
                sentence = normalize_vi_sentence(sentence)
                
                # Validate no English tokens leaked through
                from .vi_nlp import validate_vietnamese_sentence
                is_valid, english_tokens = validate_vietnamese_sentence(sentence)
                if not is_valid:
                    self.logger.error(f"CRITICAL: English tokens found in sentence: {english_tokens} - Sentence: {sentence}")
                    # In development mode, could raise an exception here
                
                descriptions.append(sentence)
            
            # If multiple objects, combine descriptions
            if len(descriptions) == 1:
                return descriptions[0]
            elif len(descriptions) <= 3:
                # List multiple objects
                return " ".join(descriptions)
            else:
                # Summarize if too many objects
                primary = descriptions[0]
                count = len(descriptions) - 1
                return f"{primary} Và còn {count} vật thể khác."
            
        except Exception as e:
            log.error("Description generation error: %s", e, exc_info=True)
            
            # Rate-limited error TTS
            global _last_error_tts
            now = time.time()
            if now - _last_error_tts > _ERROR_COOLDOWN:
                _last_error_tts = now
                # Return a single short Vietnamese error sentence (once per cooldown)
                return "Có lỗi khi mô tả cảnh vật."
            else:
                # Suppress TTS; still show overlay/log
                return None
    
    def _get_region_name(self, region: RegionType) -> str:
        """Get Vietnamese name for region."""
        region_names = {
            RegionType.FRONT: "phía trước",
            RegionType.LEFT: "bên trái",
            RegionType.RIGHT: "bên phải",
            RegionType.TOP: "phía trên",
            RegionType.BOTTOM: "phía dưới",
            RegionType.CENTER: "ở giữa",
            RegionType.FULL: "xung quanh"
        }
        return region_names.get(region, "")
    
    def _find_nearby_text(self, detection: Dict[str, Any], text_regions: List[Dict[str, Any]]) -> Optional[str]:
        """Find text near an object detection."""
        if not text_regions:
            return None
        
        det_bbox = detection['bbox']
        det_center = detection['center']
        
        # Find closest text region
        min_distance = float('inf')
        closest_text = None
        
        for text_region in text_regions:
            text_bbox = text_region['bbox']
            text_center = [
                (text_bbox[0] + text_bbox[2]) / 2,
                (text_bbox[1] + text_bbox[3]) / 2
            ]
            
            # Calculate distance between centers
            distance = np.sqrt(
                (det_center[0] - text_center[0]) ** 2 +
                (det_center[1] - text_center[1]) ** 2
            )
            
            if distance < min_distance and distance < 100:  # Within 100 pixels
                min_distance = distance
                closest_text = text_region['text']
        
        return closest_text
    
    def _create_objects_list(self, detections: List[Dict[str, Any]]) -> str:
        """Create a natural Vietnamese list of objects."""
        if not detections:
            return ""
        
        # Import Vietnamese mapping
        from .vi_nlp import map_label_en_to_vi, map_color_en_to_vi
        
        if len(detections) == 1:
            det = detections[0]
            # Use Vietnamese label only
            obj_vi = det.get('label_vi') or map_label_en_to_vi(det.get('label_en', det.get('class_name', '')))
            color_vi = map_color_en_to_vi(det.get('color', '')) or ''
            return f"{obj_vi} {color_vi}".strip()
        
        # Create list with proper Vietnamese formatting
        object_parts = []
        for detection in detections[:3]:  # Limit to first 3 for clarity
            # Use Vietnamese label only
            obj_vi = detection.get('label_vi') or map_label_en_to_vi(detection.get('label_en', detection.get('class_name', '')))
            color_vi = map_color_en_to_vi(detection.get('color', '')) or ''
            obj_desc = f"{obj_vi} {color_vi}".strip()
            object_parts.append(obj_desc)
        
        if len(detections) > 3:
            object_parts.append(f"và {len(detections) - 3} vật khác")
        
        # Join with Vietnamese conjunctions
        if len(object_parts) == 2:
            return " và ".join(object_parts)
        else:
            return ", ".join(object_parts[:-1]) + f" và {object_parts[-1]}"
    
    def _draw_annotations(self,
                         frame: np.ndarray,
                         detections: List[Dict[str, Any]],
                         text_regions: List[Dict[str, Any]],
                         roi_coords: Tuple[int, int, int, int]) -> np.ndarray:
        """Draw annotations on frame for visual feedback using YOLOv5 detector."""
        annotated = frame.copy()
        
        try:
            # Draw ROI boundary if not full frame
            x1_roi, y1_roi, x2_roi, y2_roi = roi_coords
            if not (x1_roi == 0 and y1_roi == 0 and x2_roi == frame.shape[1] and y2_roi == frame.shape[0]):
                cv2.rectangle(annotated, (x1_roi, y1_roi), (x2_roi, y2_roi), (255, 255, 0), 2)
            
            # Convert detections to format expected by detector.draw_boxes()
            yolo_detections = []
            for detection in detections:
                yolo_detection = {
                    'label': f"{detection.get('label', '')} {detection.get('color_vi', '')}",
                    'confidence': detection.get('confidence', 0.0),
                    'bbox': detection['bbox']
                }
                yolo_detections.append(yolo_detection)
            
            # Use YOLOv5 detector's draw_boxes method
            if yolo_detections:
                annotated = self.detector.draw_boxes(annotated, yolo_detections)
            
            # Draw text regions if any
            for text_region in text_regions:
                bbox = text_region['bbox']
                text = text_region.get('text', '')
                x1, y1, x2, y2 = bbox
                
                # Draw text region in blue
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 0), 2)
                
                # Draw text label
                if text:
                    cv2.putText(annotated, text[:20], (x1, y1-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            
            return annotated
            
        except Exception as e:
            self.logger.error(f"Annotation drawing error: {e}")
            return frame
    
    def _queue_speech(self, text: str, priority: bool = False):
        """Queue speech output with Vietnamese validation."""
        # CRITICAL: Validate Vietnamese sentence before speech
        from .vi_nlp import validate_vietnamese_sentence
        is_valid, english_tokens = validate_vietnamese_sentence(text)
        if not is_valid:
            self.logger.error(f"SPEECH BLOCKED: English tokens in sentence: {english_tokens} - Sentence: {text}")
            # Create a fallback Vietnamese sentence
            text = "Có thông tin được phát hiện."
        
        if self.external_speech_queue:
            self.external_speech_queue.enqueue(text)
        elif self.enable_threading and self.speech_queue:
            self.speech_queue.put((text, priority))
        elif self.speech:
            self.speech.speak_vi(text)
    
    def _update_performance_stats(self, processing_time: float):
        """Update performance tracking."""
        self.processing_times.append(processing_time)
        self.frame_count += 1
        
        # Keep only last 100 measurements
        if len(self.processing_times) > 100:
            self.processing_times.pop(0)
        
        self.last_processing_time = processing_time
    
    def _create_empty_result(self, frame: np.ndarray, region: RegionType) -> ProcessingResult:
        """Create empty result for invalid frames."""
        return ProcessingResult(
            frame=frame or np.zeros((480, 640, 3), dtype=np.uint8),
            detections=[],
            text_regions=[],
            description="",
            processing_time=0.0,
            region_processed=region
        )
    
    def _create_error_result(self, frame: np.ndarray, region: RegionType, error: str) -> ProcessingResult:
        """Create error result."""
        return ProcessingResult(
            frame=frame,
            detections=[],
            text_regions=[],
            description=f"Lỗi xử lý: {error}",
            processing_time=0.0,
            region_processed=region
        )
    
    # Public API methods
    
    def process_voice_command(self, command: str, frame: np.ndarray) -> str:
        """Process voice command and return appropriate description."""
        try:
            # Map voice commands to regions
            command_to_region = {
                'describe_front': RegionType.FRONT,
                'describe_left': RegionType.LEFT,
                'describe_right': RegionType.RIGHT,
                'read_text': RegionType.FULL
            }
            
            region = command_to_region.get(command, RegionType.FULL)
            
            # Special handling for read_text command
            if command == 'read_text':
                result = self.process_frame(frame, region, enable_ocr=True, force_description=True)
                if result.text_regions:
                    all_text = " ".join([tr['text'] for tr in result.text_regions])
                    description = f"Tôi đọc được: {all_text}"
                else:
                    description = "Không tìm thấy chữ nào trong khung hình."
            else:
                result = self.process_frame(frame, region, force_description=True)
                description = result.description or f"Không có gì đặc biệt {self._get_region_name(region)}."
            
            # Queue immediate speech
            self._queue_speech(description, priority=True)
            
            return description
            
        except Exception as e:
            self.logger.error(f"Voice command processing error: {e}")
            error_msg = "Xin lỗi, có lỗi khi xử lý lệnh."
            self._queue_speech(error_msg, priority=True)
            return error_msg
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get processing performance statistics."""
        if not self.processing_times:
            return {
                'frame_count': self.frame_count,
                'avg_processing_time': 0.0,
                'fps': 0.0,
                'last_processing_time': self.last_processing_time
            }
        
        avg_time = sum(self.processing_times) / len(self.processing_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0.0
        
        return {
            'frame_count': self.frame_count,
            'avg_processing_time': avg_time,
            'fps': fps,
            'min_processing_time': min(self.processing_times),
            'max_processing_time': max(self.processing_times),
            'last_processing_time': self.last_processing_time
        }
    
    def update_settings(self, **settings):
        """Update processor settings."""
        if 'confidence_threshold' in settings:
            self.confidence_threshold = settings['confidence_threshold']
            self.detector.update_confidence_threshold(self.confidence_threshold)
        
        if 'max_detections' in settings:
            self.max_detections = settings['max_detections']
        
        if 'enable_speech' in settings:
            self.enable_speech = settings['enable_speech']
        
        self.logger.info(f"Settings updated: {settings}")
    
    def draw_annotations(self, frame: np.ndarray, results: ProcessingResult) -> np.ndarray:
        """Public method to draw annotations from processing results."""
        region_coords = self._get_region_coordinates(frame, results.region_processed)
        return self._draw_annotations(frame, results.detections, results.text_regions, region_coords)
    
    def shutdown(self):
        """Shutdown processor and cleanup resources."""
        try:
            # Stop speech worker
            if self.speech_queue:
                self.speech_queue.put(None)  # Shutdown signal
            
            if self.speech_thread and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=2.0)
            
            # Shutdown speech synthesizer
            if self.speech:
                self.speech.stop_playback()
            
            self.logger.info("VisionProcessor shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Test vision processor
    print("Vision Processor Test")
    print("=" * 40)
    
    # Initialize processor
    processor = VisionProcessor(
        confidence_threshold=0.5,
        language='vi',
        enable_speech=False  # Disable for testing
    )
    
    # Test with webcam if available
    try:
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print("Testing with webcam (press 'q' to quit)")
            print("Press 1-5 to test different regions:")
            print("1: Front, 2: Left, 3: Right, 4: Full, 5: Read Text")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                result = processor.process_frame(frame, RegionType.FULL)
                
                # Draw annotations
                annotated = result.frame
                
                # Show performance stats
                stats = processor.get_performance_stats()
                cv2.putText(annotated, f"FPS: {stats['fps']:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Show description
                if result.description:
                    print(f"Description: {result.description}")
                
                # Display frame
                cv2.imshow('AI Eyes - Vision Processor', annotated)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('1'):
                    cmd_result = processor.process_voice_command('describe_front', frame)
                    print(f"Front: {cmd_result}")
                elif key == ord('2'):
                    cmd_result = processor.process_voice_command('describe_left', frame)
                    print(f"Left: {cmd_result}")
                elif key == ord('3'):
                    cmd_result = processor.process_voice_command('describe_right', frame)
                    print(f"Right: {cmd_result}")
                elif key == ord('4'):
                    result = processor.process_frame(frame, RegionType.FULL, force_description=True)
                    print(f"Full: {result.description}")
                elif key == ord('5'):
                    cmd_result = processor.process_voice_command('read_text', frame)
                    print(f"Text: {cmd_result}")
            
            cap.release()
            cv2.destroyAllWindows()
    
    except Exception as e:
        print(f"Test error: {e}")
    
    # Final statistics
    stats = processor.get_performance_stats()
    print(f"\nFinal Performance Stats:")
    print(f"Frames processed: {stats['frame_count']}")
    print(f"Average processing time: {stats['avg_processing_time']:.3f}s")
    print(f"Average FPS: {stats['fps']:.1f}")
    
    # Note: shutdown() removed to prevent spam logs during import
    print("Vision processor test completed!")
