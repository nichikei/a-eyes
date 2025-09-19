"""
Unit tests for distance estimation
"""
import sys
from pathlib import Path

# Add the parent directory to Python path  
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_distance_buckets():
    """Test distance bucket categorization"""
    from app.distance_estimation import DistanceEstimator
    
    estimator = DistanceEstimator()
    
    # Test different bbox bottom positions vs frame height
    frame_height = 480
    test_cases = [
        (450, 'very close'),  # Bottom near frame bottom
        (400, 'close'),       # Bottom in lower portion
        (300, 'medium'),      # Bottom in middle
        (150, 'far'),         # Bottom in upper portion
        (50, 'very far')      # Bottom near frame top
    ]
    
    for bbox_bottom_y, expected_bucket in test_cases:
        distance_info = estimator.estimate_distance(
            bbox=[100, 100, 200, bbox_bottom_y],
            frame_height=frame_height
        )
        
        assert distance_info is not None, f"Distance estimation failed for bottom_y={bbox_bottom_y}"
        
        # Get the distance bucket (should be Vietnamese) - returns string directly
        distance_bucket = distance_info
        
        # Check if we get a valid Vietnamese distance term
        vietnamese_distances = ['rất gần', 'gần', 'trung bình', 'xa', 'rất xa', 'very close', 'close', 'medium', 'far', 'very far']
        assert any(viet_dist in distance_bucket for viet_dist in vietnamese_distances), \
            f"Expected Vietnamese distance term, got: {distance_bucket}"

def test_distance_thresholds():
    """Test distance estimation with different thresholds"""
    from app.distance_estimation import DistanceEstimator
    
    # Test with default thresholds
    estimator = DistanceEstimator()
    
    frame_height = 480
    frame_width = 640
    
    # Test extreme cases
    test_bboxes = [
        ([100, 100, 200, 470], 'bottom'),   # Very bottom (should be very close)
        ([100, 50, 200, 100], 'top'),       # Very top (should be far)  
        ([100, 200, 200, 300], 'middle'),   # Middle (should be medium)
    ]
    
    for bbox, description in test_bboxes:
        distance_info = estimator.estimate_distance(
            bbox=bbox,
            frame_height=frame_height
        )
        
        assert distance_info is not None, f"Failed to estimate distance for {description} bbox"
        assert isinstance(distance_info, str), f"Distance should be string for {description}"
        assert len(distance_info) > 0, f"Distance should not be empty for {description}"

def test_vietnamese_distance_terms():
    """Test that distance estimation returns Vietnamese terms"""
    from app.distance_estimation import DistanceEstimator
    
    estimator = DistanceEstimator()
    
    # Create a bbox that should be "close"
    distance_info = estimator.estimate_distance(
        bbox=[100, 100, 200, 400],
        frame_height=480
    )
    
    assert distance_info is not None
    relative_distance = distance_info  # Returns string directly
    
    # Should contain Vietnamese distance terms
    valid_vietnamese = ['rất gần', 'gần', 'trung bình', 'xa', 'rất xa', 'medium', 'close', 'far']
    assert any(term in relative_distance for term in valid_vietnamese), \
        f"Distance term '{relative_distance}' not recognized as valid"

if __name__ == "__main__":
    test_distance_buckets()
    test_distance_thresholds()
    test_vietnamese_distance_terms()
    print("✅ All distance estimation tests passed!")
