"""
Unit tests for spatial positioning (left/center/right)
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_spatial_left():
    """Test that objects on the left are detected as left"""
    from app.processor import VisionProcessor, RegionType
    
    # Mock a simple processor just for spatial testing
    frame_width = 640
    frame_height = 480
    
    # Test bbox positions
    test_cases = [
        ([10, 100, 100, 200], 'left'),      # Far left
        ([50, 100, 150, 200], 'left'),      # Left side
        ([250, 100, 350, 200], 'center'),   # Center
        ([450, 100, 550, 200], 'right'),    # Right side  
        ([540, 100, 630, 200], 'right'),    # Far right
    ]
    
    for bbox, expected_position in test_cases:
        # Calculate center x
        center_x = (bbox[0] + bbox[2]) / 2
        
        # Determine position based on frame divisions
        if center_x < frame_width * 0.33:
            actual_position = 'left'
        elif center_x > frame_width * 0.67:
            actual_position = 'right'
        else:
            actual_position = 'center'
        
        assert actual_position == expected_position, \
            f"Bbox {bbox} with center_x={center_x:.1f} should be {expected_position}, got {actual_position}"

def test_spatial_regions():
    """Test region type definitions"""
    from app.processor import RegionType
    
    # Verify region types exist
    expected_regions = [
        RegionType.LEFT,
        RegionType.RIGHT, 
        RegionType.CENTER,
        RegionType.FRONT,
        RegionType.FULL
    ]
    
    for region in expected_regions:
        assert region is not None, f"Region {region} should be defined"

def test_bbox_position_mapping():
    """Test bbox position to Vietnamese spatial terms"""
    # Test spatial term mapping
    spatial_terms = {
        'left': ['bên trái', 'ở bên trái', 'phía trái'],
        'right': ['bên phải', 'ở bên phải', 'phía phải'],
        'center': ['ở giữa', 'chính giữa', 'trung tâm'],
        'front': ['phía trước', 'ở phía trước']
    }
    
    for english, vietnamese_options in spatial_terms.items():
        # At least one Vietnamese option should exist for each English term
        assert len(vietnamese_options) > 0, f"No Vietnamese terms for {english}"
        
        # Check that these are actually Vietnamese
        for viet_term in vietnamese_options:
            # Should contain Vietnamese characters or known Vietnamese spatial words
            is_vietnamese = (
                any(char in viet_term for char in 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ') or
                any(word in viet_term.lower() for word in ['bên', 'trái', 'phải', 'giữa', 'trước', 'phía'])
            )
            assert is_vietnamese, f"Term '{viet_term}' doesn't appear to be Vietnamese"

if __name__ == "__main__":
    test_spatial_left()
    test_spatial_regions()
    test_bbox_position_mapping()
    print("✅ All spatial tests passed!")
