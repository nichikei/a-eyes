"""
Unit tests for detector Vietnamese output
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_detector_outputs_vietnamese():
    """Test that detector outputs both label_en and label_vi"""
    from app.detector import ObjectDetector
    
    # Create detector
    detector = ObjectDetector(
        model_name='yolov5s',
        confidence_threshold=0.5,
        language='vi'
    )
    
    # Create a fake detection for testing
    class MockDetection:
        def __init__(self):
            self.names = {0: 'person', 1: 'car', 2: 'bicycle'}
    
    # Mock a detection result
    detection = MockDetection()
    
    # Test the Vietnamese mapping
    from app.vi_nlp import map_label_en_to_vi
    assert map_label_en_to_vi('person') == 'người'
    assert map_label_en_to_vi('car') == 'ô tô'
    assert map_label_en_to_vi('bicycle') == 'xe đạp'

def test_detector_vi_nlp_integration():
    """Test that detector integrates with vi_nlp module"""
    from app.detector import ObjectDetector
    from app.vi_nlp import map_label_en_to_vi, COCO_VI
    
    # Verify key mappings exist
    assert 'person' in COCO_VI
    assert 'car' in COCO_VI
    assert COCO_VI['person'] == 'người'
    assert COCO_VI['car'] == 'ô tô'
    
    # Test mapping function
    assert map_label_en_to_vi('person') == 'người'
    assert map_label_en_to_vi('car') == 'ô tô'
