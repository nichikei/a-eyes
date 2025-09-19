"""
OCR (Optical Character Recognition) Module for AI Eyes Vision Assistant

This module implements Vietnamese text recognition using EasyOCR.
It provides functionality to read text from images, with support for
region-specific OCR and comprehensive Vietnamese language processing.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import logging
import re
import time
from pathlib import Path

try:
    import easyocr
except ImportError:
    print("Warning: easyocr not installed. Please install with: pip install easyocr")
    easyocr = None

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    TESSERACT_AVAILABLE = False


class VietnameseOCR:
    """
    Vietnamese OCR system using EasyOCR and Tesseract as fallback.
    
    Features:
    - Vietnamese text recognition with high accuracy
    - Region-specific OCR (bounding box support)
    - Text preprocessing for better recognition
    - Multiple OCR engines (EasyOCR primary, Tesseract fallback)
    - Text post-processing and cleaning
    - Performance optimization for real-time use
    """
    
    def __init__(self, 
                 languages: List[str] = ['vi', 'en'],
                 gpu: bool = False,
                 confidence_threshold: float = 0.5):
        """
        Initialize Vietnamese OCR system.
        
        Args:
            languages: List of languages to recognize (['vi', 'en'])
            gpu: Use GPU for faster processing if available
            confidence_threshold: Minimum confidence for text recognition
        """
        self.languages = languages
        self.gpu = gpu
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
        
        # Initialize OCR readers
        self.easyocr_reader = None
        self.tesseract_config = None
        
        # Performance tracking
        self.ocr_times = []
        self.total_recognitions = 0
        
        # Text preprocessing settings
        self.enable_preprocessing = True
        self.enable_postprocessing = True
        
        # Initialize OCR engines
        self._initialize_easyocr()
        self._initialize_tesseract()
        
        # Vietnamese text patterns for validation
        self.vietnamese_patterns = [
            r'[àáạảãâầấậẩẫăằắặẳẵ]',  # a variations
            r'[èéẹẻẽêềếệểễ]',        # e variations
            r'[ìíịỉĩ]',              # i variations
            r'[òóọỏõôồốộổỗơờớợởỡ]', # o variations
            r'[ùúụủũưừứựửữ]',        # u variations
            r'[ỳýỵỷỹ]',             # y variations
            r'[đ]'                   # d with stroke
        ]
    
    def _initialize_easyocr(self) -> bool:
        """Initialize EasyOCR reader."""
        try:
            if easyocr is None:
                self.logger.warning("EasyOCR not available")
                return False
            
            self.logger.info("Initializing EasyOCR...")
            self.easyocr_reader = easyocr.Reader(
                lang_list=self.languages,
                gpu=self.gpu,
                verbose=False
            )
            self.logger.info("EasyOCR initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize EasyOCR: {e}")
            self.easyocr_reader = None
            return False
    
    def _initialize_tesseract(self) -> bool:
        """Initialize Tesseract OCR as fallback."""
        try:
            if not TESSERACT_AVAILABLE:
                self.logger.warning("Tesseract not available")
                return False
            
            # Configure Tesseract for Vietnamese
            self.tesseract_config = r'--oem 3 --psm 6 -l vie+eng'
            
            # Test Tesseract installation
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
            _ = pytesseract.image_to_string(test_image, config=self.tesseract_config)
            
            self.logger.info("Tesseract initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Tesseract: {e}")
            self.tesseract_config = None
            return False
    
    def read_text(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        Read Vietnamese text from image frame.
        
        Args:
            frame: Input image frame (BGR format)
            bbox: Optional bounding box (x1, y1, x2, y2) for region-specific OCR
            
        Returns:
            Recognized text as string
        """
        try:
            start_time = time.time()
            
            # Crop region if bbox is provided
            if bbox is not None:
                roi = self._crop_region(frame, bbox)
            else:
                roi = frame.copy()
            
            if roi is None or roi.size == 0:
                return ""
            
            # Preprocess image for better OCR
            if self.enable_preprocessing:
                roi = self._preprocess_image(roi)
            
            # Try EasyOCR first
            text = ""
            if self.easyocr_reader is not None:
                text = self._read_with_easyocr(roi)
            
            # Fallback to Tesseract if EasyOCR fails or not available
            if not text and self.tesseract_config is not None:
                text = self._read_with_tesseract(roi)
            
            # Post-process text
            if self.enable_postprocessing:
                text = self._postprocess_text(text)
            
            # Track performance
            ocr_time = time.time() - start_time
            self.ocr_times.append(ocr_time)
            self.total_recognitions += 1
            
            # Keep only last 100 measurements
            if len(self.ocr_times) > 100:
                self.ocr_times.pop(0)
            
            return text
            
        except Exception as e:
            self.logger.error(f"OCR error: {e}")
            return ""
    
    def _crop_region(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Crop region from frame based on bounding box.
        
        Args:
            frame: Input frame
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Cropped region or None if invalid
        """
        try:
            x1, y1, x2, y2 = bbox
            
            # Validate bounding box
            h, w = frame.shape[:2]
            x1 = max(0, min(w-1, x1))
            y1 = max(0, min(h-1, y1))
            x2 = max(x1+1, min(w, x2))
            y2 = max(y1+1, min(h, y2))
            
            # Add some padding for better OCR
            padding = 10
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)
            
            roi = frame[y1:y2, x1:x2]
            
            # Ensure minimum size for OCR
            if roi.shape[0] < 20 or roi.shape[1] < 20:
                return None
            
            return roi
            
        except Exception as e:
            self.logger.error(f"Region cropping error: {e}")
            return None
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Resize if too small (OCR works better on larger images)
            h, w = gray.shape
            if h < 50 or w < 50:
                scale_factor = max(50 / h, 50 / w, 2.0)
                new_h = int(h * scale_factor)
                new_w = int(w * scale_factor)
                gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Apply Gaussian blur to smooth the image
            blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
            
            # Threshold to binary image
            # Use Otsu's thresholding for automatic threshold selection
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Image preprocessing error: {e}")
            return image
    
    def _read_with_easyocr(self, image: np.ndarray) -> str:
        """
        Read text using EasyOCR.
        
        Args:
            image: Preprocessed image
            
        Returns:
            Recognized text
        """
        try:
            # Get OCR results
            results = self.easyocr_reader.readtext(
                image,
                detail=1,  # Return coordinates and confidence
                paragraph=False,  # Don't group into paragraphs
                width_ths=0.7,  # Width threshold for text line grouping
                height_ths=0.7,  # Height threshold for text line grouping
            )
            
            # Extract text with confidence filtering
            text_parts = []
            for (bbox, text, confidence) in results:
                if confidence >= self.confidence_threshold:
                    text_parts.append(text.strip())
            
            # Join text parts
            full_text = ' '.join(text_parts)
            
            return full_text
            
        except Exception as e:
            self.logger.error(f"EasyOCR reading error: {e}")
            return ""
    
    def _read_with_tesseract(self, image: np.ndarray) -> str:
        """
        Read text using Tesseract OCR as fallback.
        
        Args:
            image: Preprocessed image
            
        Returns:
            Recognized text
        """
        try:
            # Use Tesseract to extract text
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Tesseract reading error: {e}")
            return ""
    
    def _postprocess_text(self, text: str) -> str:
        """
        Post-process recognized text for better readability.
        
        Args:
            text: Raw OCR output
            
        Returns:
            Cleaned and processed text
        """
        if not text:
            return ""
        
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove non-printable characters
            text = re.sub(r'[^\w\s\u00C0-\u1EF9.,!?;:()\-/]', '', text)
            
            # Fix common OCR errors for Vietnamese
            text = self._fix_vietnamese_ocr_errors(text)
            
            # Remove very short "words" that are likely OCR noise
            words = text.split()
            filtered_words = [word for word in words if len(word) >= 2 or word.lower() in ['a', 'i', 'ở', 'ở']]
            text = ' '.join(filtered_words)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Text post-processing error: {e}")
            return text
    
    def _fix_vietnamese_ocr_errors(self, text: str) -> str:
        """
        Fix common OCR errors specific to Vietnamese text.
        
        Args:
            text: Text with potential OCR errors
            
        Returns:
            Text with corrections applied
        """
        # Common OCR misrecognitions in Vietnamese
        corrections = {
            # Common character confusions
            'cl': 'đ',  # 'cl' often misread as 'đ'
            'ô': 'ô',   # Ensure proper Vietnamese characters
            'â': 'â',
            'ă': 'ă',
            'ư': 'ư',
            'ê': 'ê',
            
            # Common word corrections
            'VIET NAM': 'Việt Nam',
            'viet nam': 'Việt Nam',
            'VIETNAM': 'Việt Nam',
            'vietnam': 'Việt Nam',
            'PHO': 'Phở',
            'pho': 'phở',
            'BANH MI': 'Bánh mì',
            'banh mi': 'bánh mì',
            
            # Numbers and common signs
            'DUONG': 'Đường',
            'duong': 'đường',
            'CONG TY': 'Công ty',
            'cong ty': 'công ty',
        }
        
        result = text
        for wrong, correct in corrections.items():
            result = result.replace(wrong, correct)
        
        return result
    
    def detect_text_regions(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect text regions in the frame and return their locations.
        
        Args:
            frame: Input image frame
            
        Returns:
            List of text region dictionaries with bbox, text, and confidence
        """
        try:
            if self.easyocr_reader is None:
                return []
            
            # Preprocess image
            if self.enable_preprocessing:
                processed_frame = self._preprocess_image(frame)
            else:
                processed_frame = frame
            
            # Get detailed OCR results
            results = self.easyocr_reader.readtext(
                processed_frame,
                detail=1,
                paragraph=False
            )
            
            text_regions = []
            for (bbox_coords, text, confidence) in results:
                if confidence >= self.confidence_threshold:
                    # Convert EasyOCR bbox format to our format
                    x_coords = [point[0] for point in bbox_coords]
                    y_coords = [point[1] for point in bbox_coords]
                    
                    x1, x2 = int(min(x_coords)), int(max(x_coords))
                    y1, y2 = int(min(y_coords)), int(max(y_coords))
                    
                    # Post-process text
                    if self.enable_postprocessing:
                        text = self._postprocess_text(text)
                    
                    if text.strip():  # Only include non-empty text
                        text_regions.append({
                            'bbox': (x1, y1, x2, y2),
                            'text': text.strip(),
                            'confidence': confidence,
                            'language': self._detect_language(text)
                        })
            
            return text_regions
            
        except Exception as e:
            self.logger.error(f"Text region detection error: {e}")
            return []
    
    def _detect_language(self, text: str) -> str:
        """
        Detect if text is Vietnamese or English.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code ('vi' or 'en')
        """
        # Check for Vietnamese characters
        vietnamese_char_count = 0
        total_chars = len(text)
        
        for pattern in self.vietnamese_patterns:
            vietnamese_char_count += len(re.findall(pattern, text.lower()))
        
        # If more than 10% of characters are Vietnamese-specific, consider it Vietnamese
        if total_chars > 0 and (vietnamese_char_count / total_chars) > 0.1:
            return 'vi'
        
        return 'en'
    
    def is_vietnamese_text(self, text: str) -> bool:
        """
        Check if text contains Vietnamese characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be Vietnamese
        """
        return self._detect_language(text) == 'vi'
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get OCR performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.ocr_times:
            return {
                'avg_ocr_time': 0.0,
                'total_recognitions': self.total_recognitions,
                'ocr_fps': 0.0
            }
        
        avg_time = np.mean(self.ocr_times)
        
        return {
            'avg_ocr_time': avg_time,
            'total_recognitions': self.total_recognitions,
            'ocr_fps': 1.0 / avg_time if avg_time > 0 else 0.0,
            'min_ocr_time': np.min(self.ocr_times),
            'max_ocr_time': np.max(self.ocr_times)
        }
    
    def update_confidence_threshold(self, threshold: float):
        """Update confidence threshold for text recognition."""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        self.logger.info(f"Updated OCR confidence threshold to {self.confidence_threshold}")
    
    def toggle_preprocessing(self, enable: bool):
        """Enable or disable image preprocessing."""
        self.enable_preprocessing = enable
        self.logger.info(f"OCR preprocessing {'enabled' if enable else 'disabled'}")
    
    def toggle_postprocessing(self, enable: bool):
        """Enable or disable text post-processing."""
        self.enable_postprocessing = enable
        self.logger.info(f"OCR post-processing {'enabled' if enable else 'disabled'}")


# Convenience function for direct use
def read_text(frame: np.ndarray, 
              bbox: Optional[Tuple[int, int, int, int]] = None,
              languages: List[str] = ['vi', 'en'],
              confidence_threshold: float = 0.5) -> str:
    """
    Read Vietnamese text from image frame.
    
    This is a convenience function that creates a VietnameseOCR instance
    and reads text from the specified region or full frame.
    
    Args:
        frame: Input image frame (BGR format)
        bbox: Optional bounding box (x1, y1, x2, y2) for region-specific OCR
        languages: List of languages to recognize
        confidence_threshold: Minimum confidence for text recognition
        
    Returns:
        Recognized text as string
    """
    ocr = VietnameseOCR(
        languages=languages,
        confidence_threshold=confidence_threshold
    )
    return ocr.read_text(frame, bbox)


# Example usage and testing
if __name__ == "__main__":
    # Test OCR with sample text
    ocr = VietnameseOCR(languages=['vi', 'en'])
    
    # Create test image with Vietnamese text
    test_image = np.ones((200, 600, 3), dtype=np.uint8) * 255
    
    # Add text to image (simulated - in real use, this would be from camera)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(test_image, 'Chao ban!', (50, 100), font, 2, (0, 0, 0), 3)
    cv2.putText(test_image, 'Hello World', (50, 150), font, 1, (0, 0, 0), 2)
    
    print("Vietnamese OCR Test")
    print("=" * 40)
    
    # Test full frame OCR
    full_text = ocr.read_text(test_image)
    print(f"Full frame text: '{full_text}'")
    
    # Test region-specific OCR
    region_bbox = (40, 80, 300, 120)
    region_text = ocr.read_text(test_image, region_bbox)
    print(f"Region text: '{region_text}'")
    
    # Test text region detection
    text_regions = ocr.detect_text_regions(test_image)
    print(f"\nDetected {len(text_regions)} text regions:")
    for i, region in enumerate(text_regions):
        print(f"  Region {i+1}: '{region['text']}' (confidence: {region['confidence']:.2f})")
        print(f"    Language: {region['language']}, Bbox: {region['bbox']}")
    
    # Test Vietnamese text detection
    vietnamese_samples = [
        "Xin chào",
        "Cảm ơn bạn",
        "Hello world",
        "Phở bò",
        "Bánh mì"
    ]
    
    print(f"\nVietnamese text detection:")
    for text in vietnamese_samples:
        is_vietnamese = ocr.is_vietnamese_text(text)
        print(f"  '{text}' -> {'Vietnamese' if is_vietnamese else 'English'}")
    
    # Performance stats
    stats = ocr.get_performance_stats()
    print(f"\nPerformance Stats:")
    print(f"  Total recognitions: {stats['total_recognitions']}")
    print(f"  Average OCR time: {stats['avg_ocr_time']:.3f}s")
    print(f"  OCR FPS: {stats['ocr_fps']:.1f}")
    
    # Test with webcam if available
    try:
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print(f"\nTesting with webcam (press 'q' to quit, 'space' to capture OCR)")
            print("Position text in front of camera and press space to read it")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Show frame
                cv2.imshow('Vietnamese OCR Test', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord(' '):  # Space bar to capture and read text
                    print("Reading text...")
                    text = ocr.read_text(frame)
                    if text:
                        print(f"Detected text: '{text}'")
                        
                        # Detect language
                        lang = ocr._detect_language(text)
                        print(f"Language: {'Vietnamese' if lang == 'vi' else 'English'}")
                    else:
                        print("No text detected")
            
            cap.release()
            cv2.destroyAllWindows()
    
    except Exception as e:
        print(f"Webcam test error: {e}")
    
    print("\nOCR test completed!")
