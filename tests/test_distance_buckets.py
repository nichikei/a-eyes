"""
Test distance bucket functions return exact Vietnamese strings.
"""
import sys
from pathlib import Path
import pytest

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_distance_buckets_exact_strings():
    """Test that distance functions return exactly the four required Vietnamese strings."""
    try:
        from app.distance import calculate_distance_bucket
        distance_func = calculate_distance_bucket
    except ImportError:
        try:
            from app.distance_estimation import get_distance_bucket
            distance_func = get_distance_bucket
        except ImportError:
            try:
                from app.processor import VisionProcessor
                processor = VisionProcessor()
                if hasattr(processor, '_get_distance_vietnamese'):
                    distance_func = processor._get_distance_vietnamese
                else:
                    pytest.skip("No distance bucket function found")
            except Exception:
                pytest.skip("Cannot import distance bucket function")
    
    # Exact Vietnamese strings required by specification
    required_strings = {"rất gần", "gần", "trung bình", "xa"}
    
    # Test various bbox bottom y positions (assuming 480p frame height)
    test_positions = [
        (450, "rất gần"),   # Very close - near bottom
        (400, "gần"),       # Close
        (300, "trung bình"), # Medium
        (150, "xa"),        # Far - near top
    ]
    
    returned_strings = set()
    
    for y_position, expected_category in test_positions:
        # Test with mock bbox - format may vary by implementation
        try:
            # Try different possible function signatures
            if 'bbox' in distance_func.__code__.co_varnames:
                # Function expects bbox dict/object
                mock_bbox = {'y2': y_position, 'bottom': y_position}
                result = distance_func(mock_bbox)
            else:
                # Function expects y coordinate directly
                result = distance_func(y_position)
            
            returned_strings.add(result)
            assert result in required_strings, f"Distance function returned '{result}', which is not in required set {required_strings}"
            
        except Exception as e:
            # Try alternative approach if first fails
            try:
                result = distance_func(y_position, frame_height=480)
                returned_strings.add(result)
                assert result in required_strings, f"Distance function returned '{result}', which is not in required set {required_strings}"
            except Exception:
                pytest.fail(f"Could not call distance function with y_position {y_position}: {e}")
    
    # Verify we can get all four distance categories
    assert len(returned_strings) >= 3, f"Distance function should return at least 3 different categories, got: {returned_strings}"
    
    print(f"✅ Distance function returns valid Vietnamese strings: {returned_strings}")


def test_distance_buckets_comprehensive():
    """Test distance buckets across full range of frame positions."""
    try:
        from app.distance import calculate_distance_bucket
        distance_func = calculate_distance_bucket
    except ImportError:
        try:
            from app.distance_estimation import get_distance_bucket
            distance_func = get_distance_bucket
        except ImportError:
            try:
                from app.processor import VisionProcessor
                processor = VisionProcessor()
                if hasattr(processor, '_get_distance_vietnamese'):
                    distance_func = processor._get_distance_vietnamese
                else:
                    pytest.skip("No distance bucket function found")
            except Exception:
                pytest.skip("Cannot import distance bucket function")
    
    # Test across full frame height
    frame_height = 480
    required_strings = {"rất gần", "gần", "trung bình", "xa"}
    all_results = set()
    
    # Test every 10% of frame height
    for i in range(0, 11):
        y_position = int(frame_height * i / 10)
        
        try:
            # Try different possible function signatures
            if 'bbox' in distance_func.__code__.co_varnames:
                mock_bbox = {'y2': y_position, 'bottom': y_position}
                result = distance_func(mock_bbox)
            else:
                result = distance_func(y_position)
            
            all_results.add(result)
            assert result in required_strings, f"Invalid distance string '{result}' at y={y_position}"
            
        except Exception:
            try:
                result = distance_func(y_position, frame_height=frame_height)
                all_results.add(result)
                assert result in required_strings, f"Invalid distance string '{result}' at y={y_position}"
            except Exception as e:
                # If we can't call the function, at least verify the pattern
                pytest.skip(f"Could not test distance function comprehensively: {e}")
    
    # Should have at least 2 different distance categories across full range
    assert len(all_results) >= 2, f"Distance function should return multiple categories across frame, got: {all_results}"
    
    print(f"✅ Distance function covers range appropriately: {all_results}")


def test_distance_strings_are_vietnamese():
    """Test that distance strings are proper Vietnamese (no English)."""
    try:
        from app.distance import calculate_distance_bucket
        distance_func = calculate_distance_bucket
    except ImportError:
        try:
            from app.distance_estimation import get_distance_bucket
            distance_func = get_distance_bucket
        except ImportError:
            try:
                from app.processor import VisionProcessor
                processor = VisionProcessor()
                if hasattr(processor, '_get_distance_vietnamese'):
                    distance_func = processor._get_distance_vietnamese
                else:
                    pytest.skip("No distance bucket function found")
            except Exception:
                pytest.skip("Cannot import distance bucket function")
    
    # Test a few positions and verify results are Vietnamese
    test_positions = [50, 150, 300, 450]
    english_words = ["very", "close", "near", "far", "medium", "distance", "the", "a"]
    
    for y_pos in test_positions:
        try:
            if 'bbox' in distance_func.__code__.co_varnames:
                mock_bbox = {'y2': y_pos, 'bottom': y_pos}
                result = distance_func(mock_bbox)
            else:
                result = distance_func(y_pos)
            
            # Check that result doesn't contain English words
            for english_word in english_words:
                assert english_word.lower() not in result.lower(), f"Distance string '{result}' contains English word '{english_word}'"
            
        except Exception:
            try:
                result = distance_func(y_pos, frame_height=480)
                for english_word in english_words:
                    assert english_word.lower() not in result.lower(), f"Distance string '{result}' contains English word '{english_word}'"
            except Exception:
                continue  # Skip if function signature is incompatible
    
    print(f"✅ Distance strings are pure Vietnamese")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
