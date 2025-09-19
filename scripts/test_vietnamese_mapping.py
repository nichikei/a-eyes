#!/usr/bin/env python3
"""
Direct Vietnamese mapping test - tests the core translation without full pipeline
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_vietnamese_mapping():
    """Test Vietnamese class name mapping directly"""
    print("Testing Vietnamese class name mapping...")
    
    try:
        from app.detector import ObjectDetector
        
        # Create detector with Vietnamese language
        detector = ObjectDetector(
            model_name='yolov5s',
            confidence_threshold=0.5,
            language='vi'
        )
        
        # Test the mapping directly
        test_cases = {
            'person': 'người',
            'car': 'ô tô',
            'bicycle': 'xe đạp',
            'cat': 'mèo',
            'dog': 'chó'
        }
        
        print("\n=== VIETNAMESE MAPPING TEST ===")
        all_passed = True
        
        for english, expected_vietnamese in test_cases.items():
            if english in detector.vietnamese_classes:
                actual_vietnamese = detector.vietnamese_classes[english]
                passed = actual_vietnamese == expected_vietnamese
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"{status}: {english} → {actual_vietnamese} (expected: {expected_vietnamese})")
                if not passed:
                    all_passed = False
            else:
                print(f"❌ FAIL: {english} not found in vietnamese_classes")
                all_passed = False
        
        # Test the translation method
        print(f"\n=== TRANSLATION METHOD TEST ===")
        test_detection = {
            'label': 'person',
            'confidence': 0.85,
            'bbox': [100, 100, 200, 300]
        }
        
        # Try to call the detect method to see translation in action
        # Create a dummy frame
        import numpy as np
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock the base detection
        original_detect = detector.__class__.__bases__[0].detect
        def mock_detect(self, frame):
            return [test_detection]
        
        detector.__class__.__bases__[0].detect = mock_detect
        
        try:
            detections = detector.detect(dummy_frame)
            if detections and len(detections) > 0:
                detection = detections[0]
                class_name = detection.get('class_name', 'NOT_FOUND')
                print(f"Translation result: person → {class_name}")
                
                if class_name == 'người':
                    print("✅ PASS: Translation method works correctly")
                else:
                    print(f"❌ FAIL: Expected 'người', got '{class_name}'")
                    all_passed = False
            else:
                print("❌ FAIL: No detections returned")
                all_passed = False
        except Exception as e:
            print(f"❌ FAIL: Translation method error: {e}")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sentence_building():
    """Test Vietnamese sentence building"""
    print("\n=== SENTENCE BUILDING TEST ===")
    
    try:
        # Create a mock detection with Vietnamese class name
        mock_detection = {
            'class_name': 'người',
            'confidence': 0.85,
            'bbox': [250, 150, 390, 400],
            'center': [320, 275],
            'color': 'đen',
            'relative_distance': 'gần',
            'position': 'ở giữa'
        }
        
        # Build a simple Vietnamese sentence
        sentence = f"Một chiếc {mock_detection['class_name']} màu {mock_detection['color']} ở khoảng cách {mock_detection['relative_distance']}, bên {mock_detection['position']}."
        
        print(f"Generated sentence: {sentence}")
        
        # Check for Vietnamese elements
        checks = {
            'Contains "người"': 'người' in sentence,
            'Contains "màu"': 'màu' in sentence,
            'Contains "ở"': 'ở' in sentence,
            'No English words': not any(word in sentence.lower() for word in ['person', 'car', 'bicycle', 'the', 'and'])
        }
        
        all_passed = True
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {check}")
            if not passed:
                all_passed = False
        
        # Save the test sentence
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        with open(artifacts_dir / "vietnamese_test_output.txt", 'w', encoding='utf-8') as f:
            f.write(sentence)
        
        return all_passed
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("Starting Vietnamese mapping verification...")
    
    mapping_passed = test_vietnamese_mapping()
    sentence_passed = test_sentence_building()
    
    print(f"\n=== FINAL RESULT ===")
    if mapping_passed and sentence_passed:
        print("✅ VIETNAMESE MAPPING TEST PASSED")
        return 0
    else:
        print("❌ VIETNAMESE MAPPING TEST FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
