"""
Vietnamese pipeline validator for AI Eyes Vision Assistant.
Tests the complete processing pipeline with mocked detections to ensure
all generated sentences are pure Vietnamese without English tokens.
"""

import sys
import os
import numpy as np
from typing import List, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def create_mock_detection(label_en: str, label_vi: str, color_vi: str, 
                         distance_vi: str, position_vi: str, confidence: float = 0.8) -> Dict[str, Any]:
    """Create a mock detection with Vietnamese fields."""
    return {
        'label_en': label_en,
        'label_vi': label_vi,
        'color_vi': color_vi,
        'distance_vi': distance_vi,
        'position_vi': position_vi,
        'confidence': confidence,
        'bbox': [100, 100, 200, 300],  # Mock bounding box
    }


def test_vietnamese_sentence_generation() -> bool:
    """Test Vietnamese sentence generation with various mock detections."""
    try:
        from app.processor import VisionProcessor
        from app.vi_nlp import validate_vietnamese_sentence
        
        print("🔍 Testing Vietnamese sentence generation pipeline...")
        
        # Initialize processor
        processor = VisionProcessor()
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Test cases with various Vietnamese detections
        test_cases = [
            create_mock_detection("person", "người", "xanh dương", "gần", "trung tâm"),
            create_mock_detection("car", "ô tô", "đỏ", "xa", "bên phải"),
            create_mock_detection("bicycle", "xe đạp", "xanh lá", "trung bình", "bên trái"),
            create_mock_detection("motorcycle", "xe máy", "đen", "rất gần", "trung tâm"),
            create_mock_detection("bus", "xe buýt", "vàng", "xa", "bên phải"),
            create_mock_detection("chair", "ghế", "nâu", "gần", "bên trái"),
        ]
        
        failed_sentences = []
        passed_count = 0
        
        for i, mock_detection in enumerate(test_cases):
            print(f"  Testing case {i+1}: {mock_detection['label_vi']} {mock_detection['color_vi']} {mock_detection['distance_vi']} {mock_detection['position_vi']}")
            
            # Mock the detection process
            original_process_detections = processor._process_detections
            def mock_process_detections(frame, roi_coords):
                return [mock_detection]
            
            processor._process_detections = mock_process_detections
            
            try:
                # Generate sentence
                result = processor.process_frame(frame, enable_speech=False)
                sentence = result.description if result else ""
                
                if not sentence or not sentence.strip():
                    failed_sentences.append(f"Case {i+1}: Empty sentence generated")
                    continue
                
                # Validate Vietnamese
                is_valid, english_tokens = validate_vietnamese_sentence(sentence)
                
                if not is_valid:
                    failed_sentences.append(f"Case {i+1}: English tokens {english_tokens} in sentence: '{sentence}'")
                else:
                    passed_count += 1
                    print(f"    ✅ Generated: '{sentence}'")
                
            except Exception as e:
                failed_sentences.append(f"Case {i+1}: Error generating sentence: {e}")
            finally:
                # Restore original method
                processor._process_detections = original_process_detections
        
        print(f"\n📊 Results: {passed_count}/{len(test_cases)} sentences passed Vietnamese validation")
        
        if failed_sentences:
            print("\n❌ FAILED SENTENCES:")
            for failure in failed_sentences:
                print(f"  {failure}")
            return False
        else:
            print("✅ All sentences are pure Vietnamese!")
            return True
            
    except ImportError as e:
        print(f"❌ Cannot import required modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in Vietnamese pipeline test: {e}")
        return False


def test_multi_object_sentences() -> bool:
    """Test sentence generation with multiple objects."""
    try:
        from app.processor import VisionProcessor
        from app.vi_nlp import validate_vietnamese_sentence
        
        print("\n🔍 Testing multi-object Vietnamese sentences...")
        
        processor = VisionProcessor()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Test with multiple objects
        multi_detections = [
            create_mock_detection("person", "người", "xanh dương", "gần", "bên trái", 0.9),
            create_mock_detection("car", "ô tô", "đỏ", "xa", "bên phải", 0.8),
            create_mock_detection("bicycle", "xe đạp", "xanh lá", "trung bình", "trung tâm", 0.7),
        ]
        
        # Mock detection process
        original_process_detections = processor._process_detections
        def mock_process_detections(frame, roi_coords):
            return multi_detections
        
        processor._process_detections = mock_process_detections
        
        try:
            result = processor.process_frame(frame, enable_speech=False)
            sentence = result.description if result else ""
            
            if not sentence or not sentence.strip():
                print("❌ No sentence generated for multiple objects")
                return False
            
            # Validate Vietnamese
            is_valid, english_tokens = validate_vietnamese_sentence(sentence)
            
            if not is_valid:
                print(f"❌ Multi-object sentence contains English tokens {english_tokens}: '{sentence}'")
                return False
            else:
                print(f"✅ Multi-object Vietnamese sentence: '{sentence}'")
                return True
                
        except Exception as e:
            print(f"❌ Error generating multi-object sentence: {e}")
            return False
        finally:
            processor._process_detections = original_process_detections
            
    except ImportError as e:
        print(f"❌ Cannot import modules for multi-object test: {e}")
        return False


def test_edge_cases() -> bool:
    """Test edge cases for Vietnamese sentence generation."""
    try:
        from app.processor import VisionProcessor
        from app.vi_nlp import validate_vietnamese_sentence
        
        print("\n🔍 Testing edge cases...")
        
        processor = VisionProcessor()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Test edge cases
        edge_cases = [
            # High confidence
            create_mock_detection("person", "người", "trắng", "rất gần", "trung tâm", 0.99),
            # Low confidence (but above threshold)
            create_mock_detection("car", "ô tô", "xám", "xa", "bên phải", 0.5),
            # Multiple same objects (if supported)
            # Unusual colors
            create_mock_detection("bicycle", "xe đạp", "tím", "gần", "bên trái", 0.75),
        ]
        
        failed_cases = []
        
        for i, mock_detection in enumerate(edge_cases):
            original_process_detections = processor._process_detections
            def mock_process_detections(frame, roi_coords):
                return [mock_detection]
            
            processor._process_detections = mock_process_detections
            
            try:
                result = processor.process_frame(frame, enable_speech=False)
                sentence = result.description if result else ""
                
                if sentence and sentence.strip():
                    is_valid, english_tokens = validate_vietnamese_sentence(sentence)
                    if not is_valid:
                        failed_cases.append(f"Edge case {i+1}: English tokens {english_tokens} in '{sentence}'")
                    else:
                        print(f"  ✅ Edge case {i+1}: '{sentence}'")
                else:
                    print(f"  ⚠️ Edge case {i+1}: No sentence generated (may be acceptable)")
                    
            except Exception as e:
                failed_cases.append(f"Edge case {i+1}: Error: {e}")
            finally:
                processor._process_detections = original_process_detections
        
        if failed_cases:
            print("❌ FAILED EDGE CASES:")
            for failure in failed_cases:
                print(f"  {failure}")
            return False
        else:
            print("✅ All edge cases passed!")
            return True
            
    except ImportError as e:
        print(f"❌ Cannot import modules for edge case test: {e}")
        return False


def main():
    """Run all Vietnamese pipeline validation tests."""
    print("🚀 VIETNAMESE PIPELINE VALIDATOR")
    print("=" * 50)
    
    tests = [
        ("Single object sentences", test_vietnamese_sentence_generation),
        ("Multi-object sentences", test_multi_object_sentences),
        ("Edge cases", test_edge_cases),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n🎯 FINAL RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🏆 ALL VIETNAMESE PIPELINE TESTS PASSED!")
        return True
    else:
        print("⚠️ Some Vietnamese pipeline tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
