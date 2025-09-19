#!/usr/bin/env python3
"""
Smoke test for Vietnamese output verification
Creates a synthetic image with a person detection and verifies Vietnamese labels
"""

import os
import sys
import cv2
import numpy as np
import argparse
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock external dependencies for offline testing
class MockTTS:
    def __init__(self, *args, **kwargs):
        pass
    
    def speak(self, text):
        print(f"[MOCK TTS] {text}")
        return text

class MockSpeechQueue:
    def __init__(self, *args, **kwargs):
        self._started = True
        self.spoken_texts = []
    
    def enqueue(self, text):
        self.spoken_texts.append(text)
        print(f"[MOCK SPEECH QUEUE] {text}")
    
    def start(self):
        pass

# Patch modules before importing
sys.modules['pyttsx3'] = type('MockModule', (), {'init': lambda: MockTTS()})()
sys.modules['gtts'] = type('MockModule', (), {'gTTS': MockTTS})()
sys.modules['pygame'] = type('MockModule', (), {'mixer': type('MockMixer', (), {'init': lambda: None, 'music': type('MockMusic', (), {'load': lambda x: None, 'play': lambda: None})()})()})()

# Now import the actual modules
from app.processor import VisionProcessor
from app.detector import ObjectDetector

def create_test_image():
    """Create a synthetic test image with a person-like object in the center"""
    # Create a 640x480 image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Create a simple rectangle that looks like a person (tall and narrow)
    # Position it in the center
    person_x1, person_y1 = 250, 150  # Top-left
    person_x2, person_y2 = 390, 400  # Bottom-right (center-ish)
    
    # Draw a simple "person" - head and body
    cv2.rectangle(img, (person_x1, person_y1), (person_x2, person_y2), (100, 150, 200), -1)  # Body
    cv2.circle(img, (320, 120), 30, (150, 180, 220), -1)  # Head
    
    return img

def create_mock_detection():
    """Create a mock detection with proper Vietnamese labels"""
    return [{
        'label_en': 'person',  # English label from model
        'label_vi': 'người',   # Vietnamese translation
        'class_name': 'người', # For backward compatibility
        'confidence': 0.85,
        'bbox': [250, 150, 390, 400],  # x1, y1, x2, y2 - center position
        'center': [320, 275],
        'original_label': 'person'
    }]

def add_detections_override_support(processor):
    """Add support for detection override to processor"""
    original_process_detections = processor._process_detections
    
    def process_detections_with_override(frame, roi_coords, detections_override=None):
        if detections_override is not None:
            # Use mock detections instead of running YOLO
            return detections_override
        else:
            # Use normal detection pipeline
            return original_process_detections(frame, roi_coords)
    
    processor._process_detections = process_detections_with_override
    return processor

def main():
    parser = argparse.ArgumentParser(description='Smoke test for Vietnamese output')
    parser.add_argument('--mock', action='store_true', default=True, 
                       help='Use mock detections (default: True)')
    args = parser.parse_args()
    
    print("Starting smoke test for Vietnamese output verification...")
    print(f"Mock mode: {args.mock}")
    
    # Create test image
    test_image = create_test_image()
    
    # Save test image
    artifacts_dir = Path(__file__).parent.parent / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    test_image_path = artifacts_dir / "test_input.jpg"
    cv2.imwrite(str(test_image_path), test_image)
    print(f"Created test image: {test_image_path}")
    
    try:
        # Initialize processor with mocked speech
        print("Initializing VisionProcessor...")
        processor = VisionProcessor(
            confidence_threshold=0.5,
            language='vi',
            max_detections=10,
            enable_speech=False,  # We'll mock this
            enable_threading=False,
            external_speech_queue=MockSpeechQueue()
        )
        
        # Add detection override support
        processor = add_detections_override_support(processor)
        
        # Process the frame with mock detections if requested
        print("Processing frame...")
        from app.processor import RegionType
        
        if args.mock:
            # Override detections with our mock
            mock_detections = create_mock_detection()
            print(f"Using mock detections: {mock_detections}")
            
            # Manually call the internal processing with override
            enhanced_detections = processor._process_detections(
                test_image, 
                (0, 0, test_image.shape[1], test_image.shape[0]),
                detections_override=mock_detections
            )
            
            # Build description manually using the enhanced detections
            if enhanced_detections:
                description = processor._generate_description(enhanced_detections, force_description=True)
            else:
                description = "Không phát hiện được vật thể nào."
            
            # Create result-like object
            class MockResult:
                def __init__(self, frame, description):
                    self.frame = frame
                    self.description = description
            
            result = MockResult(test_image, description)
        else:
            # Use normal processing
            result = processor.process_frame(
                test_image,
                region=RegionType.FULL,
                enable_ocr=False,
                enable_speech=False,
                force_description=True
            )
        
        # Save output image
        output_image_path = artifacts_dir / "smoke_output.jpg"
        cv2.imwrite(str(output_image_path), result.frame)
        print(f"Saved output image: {output_image_path}")
        
        # Save Vietnamese sentence
        vietnamese_sentence = result.description
        output_text_path = artifacts_dir / "smoke_output.txt"
        
        with open(output_text_path, 'w', encoding='utf-8') as f:
            f.write(vietnamese_sentence)
        
        print(f"Vietnamese sentence: {vietnamese_sentence}")
        print(f"Saved sentence to: {output_text_path}")
        
        # Verify Vietnamese content
        success = True
        checks = {
            'Contains "người" (not "person")': 'người' in vietnamese_sentence.lower(),
            'No English "person" found': 'person' not in vietnamese_sentence.lower(),
            'No English "car" found': 'car' not in vietnamese_sentence.lower(),
            'Contains Vietnamese text': any(char in vietnamese_sentence for char in 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ'),
            'Non-empty description': len(vietnamese_sentence.strip()) > 0
        }
        
        print("\n=== VERIFICATION RESULTS ===")
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {check}")
            if not passed:
                success = False
        
        # Additional Vietnamese validation
        from app.vi_nlp import validate_vietnamese_sentence
        is_valid, english_tokens = validate_vietnamese_sentence(vietnamese_sentence)
        if not is_valid:
            print(f"❌ FAIL: English tokens found: {english_tokens}")
            success = False
        else:
            print("✅ PASS: No English tokens detected")
        
        print(f"\n=== SMOKE TEST RESULT ===")
        if success:
            print("✅ SMOKE TEST PASSED: Vietnamese output verified")
            return 0
        else:
            print("❌ SMOKE TEST FAILED: Vietnamese output issues detected")
            return 1
            
    except Exception as e:
        print(f"❌ SMOKE TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
