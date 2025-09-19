"""
Unit tests for processor Vietnamese validation
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_processor_validates_vietnamese():
    """Test that processor validates Vietnamese sentences"""
    from app.vi_nlp import validate_vietnamese_sentence
    
    # Valid Vietnamese sentences
    is_valid, _ = validate_vietnamese_sentence("Tôi thấy 1 người và 2 ô tô")
    assert is_valid == True
    is_valid, _ = validate_vietnamese_sentence("Có 3 chó và 1 mèo")
    assert is_valid == True
    
    # Invalid - contains English tokens
    is_valid, english_tokens = validate_vietnamese_sentence("Tôi thấy 1 person và 2 ô tô")
    assert is_valid == False
    assert 'person' in english_tokens
    
    is_valid, english_tokens = validate_vietnamese_sentence("Có 3 dogs và 1 cat")
    assert is_valid == False
    
    is_valid, english_tokens = validate_vietnamese_sentence("I see 1 car")
    assert is_valid == False

def test_processor_uses_only_vietnamese():
    """Test that processor only uses Vietnamese labels"""
    from app.vi_nlp import map_label_en_to_vi
    
    # Create test detections
    test_detections = [
        {'label_en': 'person', 'label_vi': 'người', 'count': 1},
        {'label_en': 'car', 'label_vi': 'ô tô', 'count': 2}
    ]
    
    # Verify Vietnamese labels are correct
    for detection in test_detections:
        assert detection['label_vi'] == map_label_en_to_vi(detection['label_en'])
        # Verify no English in Vietnamese description
        from app.vi_nlp import validate_vietnamese_sentence
        test_sentence = f"Tôi thấy {detection['count']} {detection['label_vi']}"
        is_valid, english_tokens = validate_vietnamese_sentence(test_sentence)
        assert is_valid == True, f"Sentence contains English: {test_sentence}, tokens: {english_tokens}"
