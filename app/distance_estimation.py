"""
Distance Estimation Module for AI Eyes Vision Assistant

This module implements distance estimation for detected objects using multiple methods:
1. Relative positioning based on vertical position in frame
2. Focal length approximation for metric distance estimation
3. Object size-based distance estimation
4. Multi-modal distance fusion for improved accuracy
"""

import cv2
import numpy as np
import math
from typing import Tuple, Dict, Any, Optional, List
import logging
from dataclasses import dataclass


@dataclass
class CameraParameters:
    """Camera parameters for distance estimation."""
    focal_length_mm: float = 28.0  # Default focal length in mm
    sensor_height_mm: float = 15.6  # Default sensor height in mm
    frame_height_px: int = 480  # Frame height in pixels
    frame_width_px: int = 640  # Frame width in pixels
    mounting_height_m: float = 1.5  # Camera mounting height in meters
    tilt_angle_deg: float = 0.0  # Camera tilt angle in degrees


class DistanceEstimator:
    """
    Comprehensive distance estimation system for vision assistance.
    
    Features:
    - Relative distance categories based on vertical position
    - Metric distance estimation using focal length approximation
    - Object size-based distance estimation
    - Multi-modal fusion for improved accuracy
    - Vietnamese and English distance descriptions
    """
    
    # Distance categories with Vietnamese translations
    DISTANCE_CATEGORIES = {
        'very_close': {
            'en': 'very close',
            'vi': 'rất gần',
            'range_m': (0.0, 1.0),
            'description_vi': 'trong tầm với tay'
        },
        'close': {
            'en': 'close',
            'vi': 'gần',
            'range_m': (1.0, 3.0),
            'description_vi': 'gần bạn'
        },
        'medium': {
            'en': 'medium distance',
            'vi': 'khoảng cách trung bình',
            'range_m': (3.0, 8.0),
            'description_vi': 'cách vài bước chân'
        },
        'far': {
            'en': 'far',
            'vi': 'xa',
            'range_m': (8.0, 20.0),
            'description_vi': 'ở xa'
        },
        'very_far': {
            'en': 'very far',
            'vi': 'rất xa',
            'range_m': (20.0, float('inf')),
            'description_vi': 'ở rất xa'
        }
    }
    
    # Typical object heights in meters (for size-based estimation)
    OBJECT_HEIGHTS = {
        'person': 1.7,
        'car': 1.5,
        'motorcycle': 1.1,
        'bicycle': 1.0,
        'truck': 2.5,
        'bus': 3.0,
        'chair': 0.9,
        'bottle': 0.25,
        'cup': 0.1,
        'laptop': 0.02,
        'cell phone': 0.15,
        'book': 0.25,
        'backpack': 0.5,
        'handbag': 0.3,
        'suitcase': 0.6,
        'umbrella': 0.8,
        'traffic light': 3.0,
        'stop sign': 2.0,
        'bench': 0.8,
        'dining table': 0.75,
        'couch': 0.85,
        'bed': 0.6,
        'tv': 0.8,
        'refrigerator': 1.8,
        'microwave': 0.4,
        'clock': 0.3,
        'vase': 0.3,
        'potted plant': 0.5,
    }
    
    def __init__(self, 
                 camera_params: Optional[CameraParameters] = None,
                 language: str = 'vi'):
        """
        Initialize distance estimator.
        
        Args:
            camera_params: Camera parameters for metric estimation
            language: Language for distance descriptions ('en' or 'vi')
        """
        self.camera_params = camera_params or CameraParameters()
        self.language = language
        self.logger = logging.getLogger(__name__)
        
        # Calculate pixels per meter for focal length method
        self.pixels_per_meter = self._calculate_pixels_per_meter()
        
        # Distance estimation history for smoothing
        self.distance_history = {}
        self.history_size = 5
    
    def _calculate_pixels_per_meter(self) -> float:
        """Calculate pixels per meter at 1 meter distance."""
        try:
            # Focal length in pixels
            focal_length_px = (self.camera_params.focal_length_mm * self.camera_params.frame_height_px) / self.camera_params.sensor_height_mm
            
            # Pixels per meter at 1 meter distance
            pixels_per_meter_at_1m = focal_length_px
            
            return pixels_per_meter_at_1m
        
        except Exception as e:
            self.logger.error(f"Error calculating pixels per meter: {e}")
            return 400.0  # Default fallback value
    
    def estimate_distance(self, bbox: Tuple[int, int, int, int], frame_height: int) -> str:
        """
        Estimate relative distance category based on vertical position.
        
        This is the main function for relative distance estimation based on
        the assumption that objects lower in the frame are closer to the camera.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            frame_height: Height of the frame in pixels
            
        Returns:
            Distance category name in specified language
        """
        try:
            x1, y1, x2, y2 = bbox
            
            # Use bottom of bounding box for distance estimation
            bottom_y = y2
            
            # Calculate relative position (0.0 = top, 1.0 = bottom)
            relative_position = bottom_y / frame_height
            
            # Determine distance category based on vertical position
            if relative_position >= 0.8:  # Bottom 20% of frame
                category = 'very_close'
            elif relative_position >= 0.6:  # 60-80% from top
                category = 'close'
            elif relative_position >= 0.4:  # 40-60% from top
                category = 'medium'
            elif relative_position >= 0.2:  # 20-40% from top
                category = 'far'
            else:  # Top 20% of frame
                category = 'very_far'
            
            return self._get_distance_name(category)
            
        except Exception as e:
            self.logger.error(f"Distance estimation error: {e}")
            return self._get_distance_name('medium')
    
    def estimate_distance_meters(self, 
                                bbox: Tuple[int, int, int, int], 
                                object_class: str = None,
                                method: str = 'focal_length') -> Dict[str, Any]:
        """
        Estimate distance in meters using focal length approximation or object size.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            object_class: Object class name for size-based estimation
            method: Estimation method ('focal_length', 'object_size', 'fusion')
            
        Returns:
            Dictionary with distance information
        """
        try:
            x1, y1, x2, y2 = bbox
            
            if method == 'focal_length':
                distance_m = self._estimate_focal_length_distance(bbox)
            elif method == 'object_size' and object_class:
                distance_m = self._estimate_object_size_distance(bbox, object_class)
            elif method == 'fusion':
                distance_m = self._estimate_fusion_distance(bbox, object_class)
            else:
                distance_m = self._estimate_focal_length_distance(bbox)
            
            # Smooth distance using history
            distance_m = self._smooth_distance(bbox, distance_m)
            
            # Determine category from metric distance
            category = self._distance_to_category(distance_m)
            
            result = {
                'distance_meters': round(distance_m, 1),
                'distance_category': self._get_distance_name(category),
                'distance_text': self._format_distance_text(distance_m),
                'method': method,
                'confidence': self._calculate_confidence(bbox, distance_m)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Metric distance estimation error: {e}")
            return {
                'distance_meters': 5.0,
                'distance_category': self._get_distance_name('medium'),
                'distance_text': '5 mét' if self.language == 'vi' else '5 meters',
                'method': method,
                'confidence': 0.5
            }
    
    def _estimate_focal_length_distance(self, bbox: Tuple[int, int, int, int]) -> float:
        """
        Estimate distance using focal length and object height in pixels.
        
        Formula: distance = (real_height * focal_length) / pixel_height
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Estimated distance in meters
        """
        x1, y1, x2, y2 = bbox
        
        # Object height in pixels
        object_height_px = y2 - y1
        
        if object_height_px <= 0:
            return 5.0  # Default distance
        
        # Assume average human height for generic objects
        assumed_real_height = 1.7  # meters
        
        # Calculate distance using similar triangles
        # distance = (real_height * focal_length_px) / object_height_px
        distance = (assumed_real_height * self.pixels_per_meter) / object_height_px
        
        # Apply ground plane correction if camera is tilted
        if self.camera_params.tilt_angle_deg != 0:
            distance = self._apply_ground_plane_correction(distance, y2)
        
        # Reasonable bounds
        distance = max(0.3, min(50.0, distance))
        
        return distance
    
    def _estimate_object_size_distance(self, bbox: Tuple[int, int, int, int], object_class: str) -> float:
        """
        Estimate distance using known object size.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            object_class: Object class name
            
        Returns:
            Estimated distance in meters
        """
        x1, y1, x2, y2 = bbox
        
        # Get real object height
        real_height = self.OBJECT_HEIGHTS.get(object_class, 1.7)  # Default to human height
        
        # Object height in pixels
        object_height_px = y2 - y1
        
        if object_height_px <= 0:
            return 5.0
        
        # Calculate distance
        distance = (real_height * self.pixels_per_meter) / object_height_px
        
        # Apply corrections
        if self.camera_params.tilt_angle_deg != 0:
            distance = self._apply_ground_plane_correction(distance, y2)
        
        # Reasonable bounds based on object type
        if object_class in ['cell phone', 'cup', 'bottle']:
            distance = max(0.2, min(3.0, distance))  # Small objects
        elif object_class in ['person', 'car', 'motorcycle']:
            distance = max(1.0, min(50.0, distance))  # Large objects
        else:
            distance = max(0.5, min(20.0, distance))  # Medium objects
        
        return distance
    
    def _estimate_fusion_distance(self, bbox: Tuple[int, int, int, int], object_class: str = None) -> float:
        """
        Estimate distance using fusion of multiple methods.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            object_class: Object class name
            
        Returns:
            Fused distance estimate in meters
        """
        distances = []
        weights = []
        
        # Focal length method (always available)
        focal_distance = self._estimate_focal_length_distance(bbox)
        distances.append(focal_distance)
        weights.append(0.6)  # Base weight
        
        # Object size method (if object class is known)
        if object_class and object_class in self.OBJECT_HEIGHTS:
            size_distance = self._estimate_object_size_distance(bbox, object_class)
            distances.append(size_distance)
            weights.append(0.8)  # Higher weight for known objects
        
        # Perspective method (based on vertical position)
        perspective_distance = self._estimate_perspective_distance(bbox)
        distances.append(perspective_distance)
        weights.append(0.4)  # Lower weight
        
        # Weighted average
        if distances:
            weighted_sum = sum(d * w for d, w in zip(distances, weights))
            total_weight = sum(weights)
            fused_distance = weighted_sum / total_weight
        else:
            fused_distance = 5.0
        
        return fused_distance
    
    def _estimate_perspective_distance(self, bbox: Tuple[int, int, int, int]) -> float:
        """
        Estimate distance based on perspective and camera height.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Estimated distance in meters
        """
        x1, y1, x2, y2 = bbox
        
        # Distance from bottom of frame to object bottom
        bottom_distance_px = self.camera_params.frame_height_px - y2
        
        # Convert to normalized distance (0-1)
        normalized_distance = bottom_distance_px / self.camera_params.frame_height_px
        
        # Simple perspective mapping (empirically derived)
        # Objects at bottom of frame are close, objects at top are far
        if normalized_distance < 0.1:  # Very bottom
            distance = 0.5
        elif normalized_distance < 0.3:  # Lower third
            distance = 1.5
        elif normalized_distance < 0.6:  # Middle third
            distance = 5.0
        elif normalized_distance < 0.8:  # Upper third
            distance = 15.0
        else:  # Very top
            distance = 30.0
        
        return distance
    
    def _apply_ground_plane_correction(self, distance: float, bottom_y: int) -> float:
        """
        Apply ground plane correction for tilted cameras.
        
        Args:
            distance: Uncorrected distance
            bottom_y: Y coordinate of object bottom
            
        Returns:
            Corrected distance
        """
        if self.camera_params.tilt_angle_deg == 0:
            return distance
        
        # Simple trigonometric correction
        tilt_rad = math.radians(self.camera_params.tilt_angle_deg)
        
        # Calculate apparent height due to tilt
        frame_center_y = self.camera_params.frame_height_px / 2
        y_offset = bottom_y - frame_center_y
        
        # Apply correction (simplified)
        correction_factor = math.cos(tilt_rad + y_offset / self.camera_params.frame_height_px * 0.1)
        
        return distance * correction_factor
    
    def _smooth_distance(self, bbox: Tuple[int, int, int, int], current_distance: float) -> float:
        """
        Smooth distance estimates using temporal history.
        
        Args:
            bbox: Bounding box for tracking
            current_distance: Current distance estimate
            
        Returns:
            Smoothed distance
        """
        # Create a simple key for tracking (center point)
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        key = f"{center_x}_{center_y}"
        
        # Initialize history for this object
        if key not in self.distance_history:
            self.distance_history[key] = []
        
        # Add current distance to history
        self.distance_history[key].append(current_distance)
        
        # Keep only recent history
        if len(self.distance_history[key]) > self.history_size:
            self.distance_history[key].pop(0)
        
        # Return moving average
        return sum(self.distance_history[key]) / len(self.distance_history[key])
    
    def _distance_to_category(self, distance_m: float) -> str:
        """
        Convert metric distance to category.
        
        Args:
            distance_m: Distance in meters
            
        Returns:
            Distance category key
        """
        for category, info in self.DISTANCE_CATEGORIES.items():
            min_dist, max_dist = info['range_m']
            if min_dist <= distance_m < max_dist:
                return category
        
        return 'very_far'  # Default for very large distances
    
    def _calculate_confidence(self, bbox: Tuple[int, int, int, int], distance: float) -> float:
        """
        Calculate confidence score for distance estimate.
        
        Args:
            bbox: Bounding box
            distance: Estimated distance
            
        Returns:
            Confidence score (0-1)
        """
        x1, y1, x2, y2 = bbox
        
        # Base confidence
        confidence = 0.7
        
        # Higher confidence for larger objects (more pixels for analysis)
        area = (x2 - x1) * (y2 - y1)
        area_factor = min(1.0, area / (100 * 100))  # Normalize to 100x100 px
        confidence += 0.2 * area_factor
        
        # Lower confidence for very close or very far distances
        if distance < 0.5 or distance > 20.0:
            confidence *= 0.8
        
        # Ensure confidence is in valid range
        return max(0.1, min(1.0, confidence))
    
    def _get_distance_name(self, category: str) -> str:
        """
        Get distance name in specified language.
        
        Args:
            category: Distance category key
            
        Returns:
            Distance name in specified language
        """
        if category in self.DISTANCE_CATEGORIES:
            return self.DISTANCE_CATEGORIES[category][self.language]
        return category
    
    def _format_distance_text(self, distance_m: float) -> str:
        """
        Format distance as readable text.
        
        Args:
            distance_m: Distance in meters
            
        Returns:
            Formatted distance text
        """
        if self.language == 'vi':
            if distance_m < 1.0:
                return f"{int(distance_m * 100)} cm"
            else:
                return f"{distance_m:.1f} mét"
        else:
            if distance_m < 1.0:
                return f"{int(distance_m * 100)} cm"
            else:
                return f"{distance_m:.1f} meters"
    
    def get_distance_description(self, bbox: Tuple[int, int, int, int], 
                               frame_height: int, 
                               object_class: str = None,
                               include_metric: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive distance description.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            frame_height: Frame height in pixels
            object_class: Object class for size-based estimation
            include_metric: Include metric distance estimation
            
        Returns:
            Complete distance information
        """
        try:
            # Get relative distance
            relative_distance = self.estimate_distance(bbox, frame_height)
            
            result = {
                'relative_distance': relative_distance,
                'position_description': self._get_position_description(bbox, frame_height)
            }
            
            # Add metric distance if requested
            if include_metric:
                metric_info = self.estimate_distance_meters(bbox, object_class, method='fusion')
                result.update(metric_info)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Distance description error: {e}")
            return {
                'relative_distance': self._get_distance_name('medium'),
                'position_description': 'ở giữa' if self.language == 'vi' else 'in the middle',
                'distance_meters': 5.0,
                'distance_text': '5 mét' if self.language == 'vi' else '5 meters'
            }
    
    def _get_position_description(self, bbox: Tuple[int, int, int, int], frame_height: int) -> str:
        """
        Get position description (top, middle, bottom).
        
        Args:
            bbox: Bounding box
            frame_height: Frame height
            
        Returns:
            Position description
        """
        x1, y1, x2, y2 = bbox
        center_y = (y1 + y2) / 2
        relative_y = center_y / frame_height
        
        if self.language == 'vi':
            if relative_y < 0.33:
                return 'ở phía trên'
            elif relative_y < 0.67:
                return 'ở giữa'
            else:
                return 'ở phía dưới'
        else:
            if relative_y < 0.33:
                return 'at the top'
            elif relative_y < 0.67:
                return 'in the middle'
            else:
                return 'at the bottom'
    
    def update_camera_parameters(self, params: CameraParameters):
        """Update camera parameters and recalculate derived values."""
        self.camera_params = params
        self.pixels_per_meter = self._calculate_pixels_per_meter()
        self.logger.info("Camera parameters updated")
    
    def update_language(self, language: str):
        """Update language for distance descriptions."""
        self.language = language
        self.logger.info(f"Distance estimation language updated to: {language}")


# Convenience functions for direct use
def estimate_distance(bbox: Tuple[int, int, int, int], frame_height: int, language: str = 'vi') -> str:
    """
    Estimate relative distance category.
    
    Args:
        bbox: Bounding box (x1, y1, x2, y2)
        frame_height: Frame height in pixels
        language: Language for result ('en' or 'vi')
        
    Returns:
        Distance category in specified language
    """
    estimator = DistanceEstimator(language=language)
    return estimator.estimate_distance(bbox, frame_height)


def estimate_distance_meters(bbox: Tuple[int, int, int, int], 
                           object_class: str = None,
                           language: str = 'vi') -> Dict[str, Any]:
    """
    Estimate distance in meters.
    
    Args:
        bbox: Bounding box (x1, y1, x2, y2)
        object_class: Object class for size-based estimation
        language: Language for result ('en' or 'vi')
        
    Returns:
        Distance information dictionary
    """
    estimator = DistanceEstimator(language=language)
    return estimator.estimate_distance_meters(bbox, object_class, method='fusion')


# Example usage and testing
if __name__ == "__main__":
    # Test distance estimation with sample bounding boxes
    estimator = DistanceEstimator(language='vi')
    
    # Create test scenarios
    frame_height = 480
    test_cases = [
        # (bbox, object_class, expected_category)
        ((100, 400, 200, 470), 'person', 'very_close'),  # Bottom of frame
        ((150, 300, 250, 400), 'person', 'close'),       # Lower middle
        ((200, 200, 300, 300), 'car', 'medium'),         # Center
        ((250, 100, 350, 200), 'bicycle', 'far'),        # Upper middle
        ((300, 20, 400, 100), 'motorcycle', 'very_far'), # Top of frame
    ]
    
    print("Distance Estimation Test Results:")
    print("=" * 50)
    
    for i, (bbox, obj_class, expected) in enumerate(test_cases):
        # Test relative distance
        relative_dist = estimator.estimate_distance(bbox, frame_height)
        
        # Test metric distance
        metric_info = estimator.estimate_distance_meters(bbox, obj_class, method='fusion')
        
        # Test comprehensive description
        full_desc = estimator.get_distance_description(bbox, frame_height, obj_class)
        
        print(f"\nTest Case {i+1}:")
        print(f"  Object: {obj_class}")
        print(f"  Bbox: {bbox}")
        print(f"  Relative Distance: {relative_dist}")
        print(f"  Metric Distance: {metric_info['distance_text']}")
        print(f"  Position: {full_desc['position_description']}")
        print(f"  Confidence: {metric_info['confidence']:.2f}")
        print(f"  Method: {metric_info['method']}")
    
    # Test different languages
    print(f"\n{'='*50}")
    print("Language Comparison:")
    estimator_en = DistanceEstimator(language='en')
    
    test_bbox = (150, 350, 250, 450)
    
    vi_result = estimator.estimate_distance(test_bbox, frame_height)
    en_result = estimator_en.estimate_distance(test_bbox, frame_height)
    
    print(f"Vietnamese: {vi_result}")
    print(f"English: {en_result}")
    
    print(f"\nDistance estimation test completed!")
    
    # Performance test
    import time
    
    print(f"\n{'='*50}")
    print("Performance Test:")
    
    start_time = time.time()
    iterations = 1000
    
    for _ in range(iterations):
        bbox = (100 + _ % 100, 200 + _ % 200, 200 + _ % 100, 300 + _ % 200)
        _ = estimator.estimate_distance(bbox, frame_height)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / iterations * 1000  # Convert to milliseconds
    
    print(f"Average estimation time: {avg_time:.2f} ms")
    print(f"Estimated FPS capability: {1000/avg_time:.1f} FPS")
