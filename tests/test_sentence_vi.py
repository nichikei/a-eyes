"""
Test Vietnamese sentence generation from mocked detections.
Verifies that generated sentences contain only Vietnamese tokens.
"""
import sys
from pathlib import Path
import pytest

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_vietnamese_sentence_generation():
    """Test that processor generates pure Vietnamese sentences from mocked detections."""
    try:
        from app.processor import VisionProcessor
        import numpy as np
        
        # Initialize processor
        processor = VisionProcessor()
        
        # Create mock frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create mock detection with Vietnamese fields
        mock_detection = {
            'label_en': 'person',
            'label_vi': 'người',
            'color_vi': 'xanh dương',
            'distance_vi': 'gần',
            'position_vi': 'trung tâm',
            'confidence': 0.85,
            'bbox': [100, 100, 200, 300]
        }
        
        # Mock the detection process to return our controlled data
        original_process_detections = processor._process_detections
        def mock_process_detections(frame, roi_coords):
            return [mock_detection]
        
        processor._process_detections = mock_process_detections
        
        # Process frame and get description
        result = processor.process_frame(frame, enable_speech=False)
        sentence = result.description if result else ""
        
        # Restore original method
        processor._process_detections = original_process_detections
        
        # Validate sentence is not empty
        assert sentence and sentence.strip(), f"Generated sentence is empty: '{sentence}'"
        
        # Test Vietnamese validation
        from app.vi_nlp import validate_vietnamese_sentence
        is_valid, english_tokens = validate_vietnamese_sentence(sentence)
        
        # Assert sentence is pure Vietnamese
        assert is_valid, f"Generated sentence contains English tokens {english_tokens}: '{sentence}'"
        
        # Verify sentence contains Vietnamese content
        assert 'người' in sentence, f"Sentence should contain Vietnamese label 'người': '{sentence}'"
        
        print(f"✅ Generated pure Vietnamese sentence: '{sentence}'")
        
    except ImportError as e:
        pytest.skip(f"Cannot import required modules: {e}")
    except Exception as e:
        pytest.fail(f"Error in Vietnamese sentence generation test: {e}")


def test_sentence_rejects_english_tokens():
    """Test that sentence validation correctly identifies English tokens."""
    try:
        from app.vi_nlp import validate_vietnamese_sentence
        
        # Test sentences with English words
        test_cases = [
            ("Có một person ở trung tâm", False, ["person"]),
            ("A red car is moving", False, ["A", "red", "car", "is", "moving"]),
            ("Xe ô tô màu đỏ đang di chuyển", True, []),
            ("The người is walking", False, ["The", "is", "walking"]),
            ("Người đang đi bộ", True, []),
            ("left side có xe", False, ["left", "side"]),
            ("bên trái có xe", True, []),
        ]
        
        for sentence, expected_valid, expected_tokens in test_cases:
            is_valid, tokens = validate_vietnamese_sentence(sentence)
            
            assert is_valid == expected_valid, f"Sentence '{sentence}': expected valid={expected_valid}, got {is_valid}"
            
            # Check that expected English tokens are detected
            for expected_token in expected_tokens:
                assert expected_token in tokens, f"Expected token '{expected_token}' not detected in '{sentence}'"
        
        print(f"✅ Vietnamese validation correctly identifies English tokens")
        
    except ImportError:
        pytest.skip("Cannot import Vietnamese validation function")


def test_sentence_with_multiple_objects():
    """Test sentence generation with multiple Vietnamese objects."""
    try:
        from app.processor import VisionProcessor
        import numpy as np
        
        processor = VisionProcessor()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock multiple detections
        mock_detections = [
            {
                'label_en': 'person',
                'label_vi': 'người',
                'color_vi': 'xanh dương',
                'distance_vi': 'gần',
                'position_vi': 'trung tâm',
                'confidence': 0.9,
                'bbox': [100, 100, 200, 300]
            },
            {
                'label_en': 'car',
                'label_vi': 'ô tô',
                'color_vi': 'đỏ',
                'distance_vi': 'xa',
                'position_vi': 'bên phải',
                'confidence': 0.8,
                'bbox': [300, 50, 450, 200]
            }
        ]
        
        # Mock detection process
        original_process_detections = processor._process_detections
        def mock_process_detections(frame, roi_coords):
            return mock_detections
        
        processor._process_detections = mock_process_detections
        
        # Generate sentence
        result = processor.process_frame(frame, enable_speech=False)
        sentence = result.description if result else ""
        
        # Restore original
        processor._process_detections = original_process_detections
        
        # Validate
        assert sentence and sentence.strip(), f"No sentence generated for multiple objects"
        
        from app.vi_nlp import validate_vietnamese_sentence
        is_valid, english_tokens = validate_vietnamese_sentence(sentence)
        
        assert is_valid, f"Multi-object sentence contains English tokens {english_tokens}: '{sentence}'"
        
        # Should mention both objects
        assert 'người' in sentence or 'ô tô' in sentence, f"Sentence should mention detected objects: '{sentence}'"
        
        print(f"✅ Multi-object Vietnamese sentence: '{sentence}'")
        
    except ImportError:
        pytest.skip("Cannot import required modules")
    except Exception as e:
        pytest.fail(f"Error in multi-object sentence test: {e}")


def test_color_and_position_vietnamese():
    """Test that color and position descriptions are in Vietnamese."""
    try:
        from app.processor import VisionProcessor
        import numpy as np
        
        processor = VisionProcessor()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock detection with specific color and position
        mock_detection = {
            'label_en': 'car',
            'label_vi': 'ô tô',
            'color_vi': 'xanh lá',  # Green in Vietnamese
            'distance_vi': 'trung bình',
            'position_vi': 'bên trái',  # Left side in Vietnamese
            'confidence': 0.85,
            'bbox': [50, 200, 150, 400]
        }
        
        # Mock detection process
        original_process_detections = processor._process_detections
        def mock_process_detections(frame, roi_coords):
            return [mock_detection]
        
        processor._process_detections = mock_process_detections
        
        # Generate sentence
        result = processor.process_frame(frame, enable_speech=False)
        sentence = result.description if result else ""
        
        # Restore original
        processor._process_detections = original_process_detections
        
        # Validate Vietnamese content
        from app.vi_nlp import validate_vietnamese_sentence
        is_valid, english_tokens = validate_vietnamese_sentence(sentence)
        
        assert is_valid, f"Sentence with color/position contains English: {english_tokens}: '{sentence}'"
        
        # Should not contain English color or position words
        english_color_position = ["green", "blue", "red", "left", "right", "center", "middle"]
        for english_word in english_color_position:
            assert english_word.lower() not in sentence.lower(), f"Sentence contains English word '{english_word}': '{sentence}'"
        
        print(f"✅ Color/position sentence is pure Vietnamese: '{sentence}'")
        
    except ImportError:
        pytest.skip("Cannot import required modules")
    except Exception as e:
        pytest.fail(f"Error in color/position test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
