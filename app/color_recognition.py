"""
Color Recognition Module for AI Eyes Vision Assistant

This module implements color detection and recognition for detected objects.
It uses k-means clustering to find dominant colors and maps them to human-readable
color names in both English and Vietnamese.
"""

import cv2
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
import logging
from sklearn.cluster import KMeans
import webcolors
from collections import Counter
import math


class ColorRecognizer:
    """
    Advanced color recognition system for object color detection.
    
    Features:
    - K-means clustering for dominant color extraction
    - Comprehensive color name mapping (English/Vietnamese)
    - HSV-based color analysis for better accuracy
    - Noise filtering and edge detection
    - Multiple color detection strategies
    """
    
    # Comprehensive color mapping with Vietnamese translations
    COLOR_NAMES = {
        # Basic colors
        'red': {'vi': 'đỏ', 'rgb': (255, 0, 0), 'hsv_range': [(0, 10), (160, 180)]},
        'green': {'vi': 'xanh lá cây', 'rgb': (0, 255, 0), 'hsv_range': [(40, 80)]},
        'blue': {'vi': 'xanh dương', 'rgb': (0, 0, 255), 'hsv_range': [(100, 130)]},
        'yellow': {'vi': 'vàng', 'rgb': (255, 255, 0), 'hsv_range': [(20, 40)]},
        'orange': {'vi': 'cam', 'rgb': (255, 165, 0), 'hsv_range': [(10, 20)]},
        'purple': {'vi': 'tím', 'rgb': (128, 0, 128), 'hsv_range': [(130, 160)]},
        'pink': {'vi': 'hồng', 'rgb': (255, 192, 203), 'hsv_range': [(160, 180)]},
        'cyan': {'vi': 'xanh lơ', 'rgb': (0, 255, 255), 'hsv_range': [(80, 100)]},
        
        # Neutral colors
        'white': {'vi': 'trắng', 'rgb': (255, 255, 255), 'hsv_range': None},
        'black': {'vi': 'đen', 'rgb': (0, 0, 0), 'hsv_range': None},
        'gray': {'vi': 'xám', 'rgb': (128, 128, 128), 'hsv_range': None},
        'grey': {'vi': 'xám', 'rgb': (128, 128, 128), 'hsv_range': None},
        
        # Extended colors
        'brown': {'vi': 'nâu', 'rgb': (165, 42, 42), 'hsv_range': [(10, 20)]},
        'maroon': {'vi': 'đỏ thẫm', 'rgb': (128, 0, 0), 'hsv_range': [(0, 10)]},
        'navy': {'vi': 'xanh navy', 'rgb': (0, 0, 128), 'hsv_range': [(110, 130)]},
        'olive': {'vi': 'xanh ô liu', 'rgb': (128, 128, 0), 'hsv_range': [(30, 40)]},
        'lime': {'vi': 'xanh chanh', 'rgb': (0, 255, 0), 'hsv_range': [(60, 80)]},
        'aqua': {'vi': 'xanh nước biển', 'rgb': (0, 255, 255), 'hsv_range': [(85, 95)]},
        'teal': {'vi': 'xanh teal', 'rgb': (0, 128, 128), 'hsv_range': [(90, 100)]},
        'silver': {'vi': 'bạc', 'rgb': (192, 192, 192), 'hsv_range': None},
        'gold': {'vi': 'vàng kim', 'rgb': (255, 215, 0), 'hsv_range': [(45, 55)]},
        
        # Light variations
        'light_blue': {'vi': 'xanh nhạt', 'rgb': (173, 216, 230), 'hsv_range': [(100, 120)]},
        'light_green': {'vi': 'xanh lá nhạt', 'rgb': (144, 238, 144), 'hsv_range': [(60, 80)]},
        'light_red': {'vi': 'đỏ nhạt', 'rgb': (255, 182, 193), 'hsv_range': [(350, 10)]},
        'light_yellow': {'vi': 'vàng nhạt', 'rgb': (255, 255, 224), 'hsv_range': [(55, 65)]},
        
        # Dark variations
        'dark_blue': {'vi': 'xanh đậm', 'rgb': (0, 0, 139), 'hsv_range': [(110, 130)]},
        'dark_green': {'vi': 'xanh lá đậm', 'rgb': (0, 100, 0), 'hsv_range': [(50, 70)]},
        'dark_red': {'vi': 'đỏ đậm', 'rgb': (139, 0, 0), 'hsv_range': [(0, 10)]},
        'dark_gray': {'vi': 'xám đậm', 'rgb': (64, 64, 64), 'hsv_range': None},
    }
    
    def __init__(self, language: str = 'en'):
        """
        Initialize color recognizer.
        
        Args:
            language: Language for color names ('en' for English, 'vi' for Vietnamese)
        """
        self.language = language
        self.logger = logging.getLogger(__name__)
        
        # Color analysis parameters
        self.n_clusters = 5  # Number of dominant colors to extract
        self.min_area_ratio = 0.01  # Minimum area ratio for color consideration
        self.edge_exclusion_ratio = 0.1  # Exclude edges to avoid background noise
        
    def get_dominant_color(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> str:
        """
        Extract dominant color from object region using k-means clustering.
        
        Args:
            frame: Input image frame (BGR format)
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Dominant color name in specified language
        """
        try:
            # Extract object region
            x1, y1, x2, y2 = bbox
            
            # Validate bounding box
            if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0:
                return self._get_color_name('gray')
            
            h, w = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            # Extract region of interest
            roi = frame[y1:y2, x1:x2]
            
            if roi.size == 0:
                return self._get_color_name('gray')
            
            # Apply preprocessing to improve color detection
            roi_processed = self._preprocess_roi(roi)
            
            # Get dominant colors using k-means
            dominant_colors = self._extract_dominant_colors_kmeans(roi_processed)
            
            if not dominant_colors:
                return self._get_color_name('gray')
            
            # Find the best matching color name
            best_color = self._find_best_color_match(dominant_colors[0])
            
            return self._get_color_name(best_color)
            
        except Exception as e:
            self.logger.error(f"Color detection error: {e}")
            return self._get_color_name('gray')
    
    def _preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        """
        Preprocess ROI to improve color detection accuracy.
        
        Args:
            roi: Region of interest
            
        Returns:
            Preprocessed ROI
        """
        # Remove edge pixels to avoid background contamination
        h, w = roi.shape[:2]
        edge_h = max(1, int(h * self.edge_exclusion_ratio))
        edge_w = max(1, int(w * self.edge_exclusion_ratio))
        
        roi_center = roi[edge_h:h-edge_h, edge_w:w-edge_w]
        
        if roi_center.size == 0:
            roi_center = roi
        
        # Apply Gaussian blur to reduce noise
        roi_blurred = cv2.GaussianBlur(roi_center, (5, 5), 0)
        
        # Optional: Apply bilateral filter for edge-preserving smoothing
        roi_filtered = cv2.bilateralFilter(roi_blurred, 9, 75, 75)
        
        return roi_filtered
    
    def _extract_dominant_colors_kmeans(self, roi: np.ndarray) -> List[Tuple[int, int, int]]:
        """
        Extract dominant colors using k-means clustering.
        
        Args:
            roi: Region of interest
            
        Returns:
            List of dominant colors in RGB format, sorted by frequency
        """
        try:
            # Reshape image to be a list of pixels
            pixels = roi.reshape(-1, 3)
            
            # Convert BGR to RGB
            pixels_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB).reshape(-1, 3)
            
            # Filter out very dark and very bright pixels (likely shadows/highlights)
            pixel_mask = np.logical_and(
                np.mean(pixels_rgb, axis=1) > 30,   # Not too dark
                np.mean(pixels_rgb, axis=1) < 225   # Not too bright
            )
            
            filtered_pixels = pixels_rgb[pixel_mask]
            
            if len(filtered_pixels) < 10:  # Not enough valid pixels
                filtered_pixels = pixels_rgb
            
            # Determine optimal number of clusters
            n_clusters = min(self.n_clusters, len(filtered_pixels))
            if n_clusters < 1:
                return []
            
            # Apply k-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(filtered_pixels)
            
            # Get cluster centers (dominant colors)
            colors = kmeans.cluster_centers_.astype(int)
            
            # Get cluster labels and count frequencies
            labels = kmeans.labels_
            label_counts = Counter(labels)
            
            # Sort colors by frequency
            sorted_colors = []
            for label, count in label_counts.most_common():
                color = tuple(colors[label])
                sorted_colors.append(color)
            
            return sorted_colors
            
        except Exception as e:
            self.logger.error(f"K-means clustering error: {e}")
            return []
    
    def _find_best_color_match(self, rgb_color: Tuple[int, int, int]) -> str:
        """
        Find the best matching color name for an RGB color.
        
        Args:
            rgb_color: RGB color tuple
            
        Returns:
            Best matching color name
        """
        try:
            # First try exact webcolors match
            try:
                color_name = webcolors.rgb_to_name(rgb_color)
                return color_name.lower()
            except ValueError:
                pass
            
            # Convert to HSV for better color analysis
            rgb_array = np.uint8([[rgb_color]])
            hsv_color = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)[0][0]
            h, s, v = hsv_color
            
            # Handle grayscale colors first
            if s < 30:  # Low saturation = grayscale
                if v < 50:
                    return 'black'
                elif v > 200:
                    return 'white'
                elif v < 100:
                    return 'dark_gray'
                else:
                    return 'gray'
            
            # Handle low brightness
            if v < 50:
                return 'black'
            
            # Find best match based on HSV ranges
            best_match = 'gray'
            min_distance = float('inf')
            
            for color_name, color_info in self.COLOR_NAMES.items():
                if color_info['hsv_range'] is None:
                    continue
                
                # Check if hue falls within any of the ranges for this color
                hsv_ranges = color_info['hsv_range']
                if not isinstance(hsv_ranges[0], tuple):
                    hsv_ranges = [hsv_ranges]
                
                for hue_range in hsv_ranges:
                    hue_min, hue_max = hue_range
                    
                    # Handle hue wraparound (red color)
                    if hue_min > hue_max:  # e.g., (160, 10) for red
                        in_range = h >= hue_min or h <= hue_max
                    else:
                        in_range = hue_min <= h <= hue_max
                    
                    if in_range:
                        # Calculate color distance
                        target_rgb = color_info['rgb']
                        distance = self._calculate_color_distance(rgb_color, target_rgb)
                        
                        if distance < min_distance:
                            min_distance = distance
                            best_match = color_name
            
            # If no HSV match found, use RGB distance
            if best_match == 'gray':
                best_match = self._find_closest_rgb_match(rgb_color)
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"Color matching error: {e}")
            return 'gray'
    
    def _calculate_color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """
        Calculate Euclidean distance between two RGB colors.
        
        Args:
            color1: First RGB color
            color2: Second RGB color
            
        Returns:
            Distance between colors
        """
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        return math.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)
    
    def _find_closest_rgb_match(self, rgb_color: Tuple[int, int, int]) -> str:
        """
        Find closest color match using RGB distance.
        
        Args:
            rgb_color: RGB color to match
            
        Returns:
            Closest color name
        """
        min_distance = float('inf')
        closest_color = 'gray'
        
        for color_name, color_info in self.COLOR_NAMES.items():
            target_rgb = color_info['rgb']
            distance = self._calculate_color_distance(rgb_color, target_rgb)
            
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name
        
        return closest_color
    
    def _get_color_name(self, color_key: str) -> str:
        """
        Get color name in specified language.
        
        Args:
            color_key: Color key from COLOR_NAMES
            
        Returns:
            Color name in specified language
        """
        if color_key in self.COLOR_NAMES:
            if self.language == 'vi':
                return self.COLOR_NAMES[color_key]['vi']
            else:
                return color_key.replace('_', ' ')
        return color_key.replace('_', ' ')
    
    def get_color_palette(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], n_colors: int = 3) -> List[Dict[str, Any]]:
        """
        Get color palette (multiple dominant colors) from object region.
        
        Args:
            frame: Input image frame
            bbox: Bounding box (x1, y1, x2, y2)
            n_colors: Number of colors to extract
            
        Returns:
            List of color information dictionaries
        """
        try:
            x1, y1, x2, y2 = bbox
            roi = frame[y1:y2, x1:x2]
            
            if roi.size == 0:
                return []
            
            roi_processed = self._preprocess_roi(roi)
            
            # Temporarily increase cluster count
            original_clusters = self.n_clusters
            self.n_clusters = min(n_colors, 8)
            
            dominant_colors = self._extract_dominant_colors_kmeans(roi_processed)
            
            # Restore original cluster count
            self.n_clusters = original_clusters
            
            color_palette = []
            for i, rgb_color in enumerate(dominant_colors[:n_colors]):
                color_name = self._find_best_color_match(rgb_color)
                color_info = {
                    'name': self._get_color_name(color_name),
                    'rgb': rgb_color,
                    'rank': i + 1,
                    'percentage': None  # Could calculate if needed
                }
                color_palette.append(color_info)
            
            return color_palette
            
        except Exception as e:
            self.logger.error(f"Color palette extraction error: {e}")
            return []
    
    def update_language(self, language: str):
        """Update language for color names."""
        self.language = language
        self.logger.info(f"Color recognition language updated to: {language}")


# Convenience function for direct use
def get_dominant_color(frame: np.ndarray, bbox: Tuple[int, int, int, int], language: str = 'en') -> str:
    """
    Extract dominant color from object region.
    
    This is a convenience function that creates a ColorRecognizer instance
    and extracts the dominant color from the specified region.
    
    Args:
        frame: Input image frame (BGR format)
        bbox: Bounding box (x1, y1, x2, y2)
        language: Language for color name ('en' or 'vi')
        
    Returns:
        Dominant color name in specified language
    """
    recognizer = ColorRecognizer(language=language)
    return recognizer.get_dominant_color(frame, bbox)


# Example usage and testing
if __name__ == "__main__":
    # Test color recognition with sample colors
    recognizer = ColorRecognizer(language='vi')  # Vietnamese names
    
    # Create test image with colored rectangles
    test_image = np.zeros((400, 600, 3), dtype=np.uint8)
    
    # Add colored rectangles
    colors_rgb = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green  
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 165, 0),  # Orange
        (128, 0, 128),  # Purple
    ]
    
    rectangles = [
        (50, 50, 150, 150),
        (200, 50, 300, 150),
        (350, 50, 450, 150),
        (50, 200, 150, 300),
        (200, 200, 300, 300),
        (350, 200, 450, 300),
    ]
    
    # Draw rectangles and test color detection
    for i, (color, rect) in enumerate(zip(colors_rgb, rectangles)):
        x1, y1, x2, y2 = rect
        # Convert RGB to BGR for OpenCV
        bgr_color = (color[2], color[1], color[0])
        cv2.rectangle(test_image, (x1, y1), (x2, y2), bgr_color, -1)
        
        # Detect color
        detected_color = recognizer.get_dominant_color(test_image, rect)
        print(f"Rectangle {i+1}: Expected RGB{color} -> Detected: {detected_color}")
        
        # Get color palette
        palette = recognizer.get_color_palette(test_image, rect, n_colors=2)
        print(f"  Palette: {[c['name'] for c in palette]}")
    
    print("\nColor recognition test completed!")
    
    # Test with webcam if available
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print("\nTesting with webcam (press 'q' to quit)")
            print("Click on objects to detect their color")
            
            def mouse_callback(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    # Create a small region around click point
                    bbox = (max(0, x-25), max(0, y-25), x+25, y+25)
                    color = recognizer.get_dominant_color(param, bbox)
                    print(f"Clicked color: {color}")
            
            cv2.namedWindow('Color Recognition Test')
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                cv2.setMouseCallback('Color Recognition Test', mouse_callback, frame)
                cv2.imshow('Color Recognition Test', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
    
    except Exception as e:
        print(f"Webcam test error: {e}")
