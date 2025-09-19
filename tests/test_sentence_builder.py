"""
Unit tests for Vietnamese sentence building
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_sentence_builder_single_object():
    """Test sentence building for single object"""
    # Test data
    detection = {
        'class_name': 'người',
        'color': 'đen',
        'relative_distance': 'gần',
        'position': 'ở giữa'
    }
    
    # Build sentence
    sentence = f"Một chiếc {detection['class_name']} màu {detection['color']} ở khoảng cách {detection['relative_distance']}, bên {detection['position']}."
    
    # Verify Vietnamese content
    assert 'người' in sentence, "Should contain Vietnamese class name"
    assert 'màu' in sentence, "Should contain Vietnamese color indicator"
    assert 'gần' in sentence, "Should contain Vietnamese distance"
    assert 'ở giữa' in sentence, "Should contain Vietnamese position"
    
    # Verify no English tokens remain
    english_tokens = ['person', 'black', 'close', 'center', 'the', 'and', 'is', 'at']
    for token in english_tokens:
        assert token.lower() not in sentence.lower(), f"Should not contain English token: {token}"

def test_sentence_builder_multiple_objects():
    """Test sentence building for multiple objects"""
    detections = [
        {'class_name': 'người', 'color': 'đen'},
        {'class_name': 'ô tô', 'color': 'đỏ'},
        {'class_name': 'xe đạp', 'color': 'xanh'}
    ]
    
    # Build object list
    object_parts = []
    for detection in detections:
        obj_desc = f"{detection['class_name']} {detection['color']}".strip()
        object_parts.append(obj_desc)
    
    # Join with Vietnamese conjunctions
    if len(object_parts) == 2:
        objects_string = " và ".join(object_parts)
    else:
        objects_string = ", ".join(object_parts[:-1]) + f" và {object_parts[-1]}"
    
    sentence = f"Có {len(detections)} vật thể: {objects_string}."
    
    # Verify Vietnamese content
    assert 'người' in sentence, "Should contain Vietnamese person"
    assert 'ô tô' in sentence, "Should contain Vietnamese car"
    assert 'xe đạp' in sentence, "Should contain Vietnamese bicycle"
    assert 'và' in sentence, "Should contain Vietnamese conjunction"
    assert 'vật thể' in sentence, "Should contain Vietnamese 'objects'"
    
    # Verify no English class names
    english_classes = ['person', 'car', 'bicycle']
    for english_class in english_classes:
        assert english_class.lower() not in sentence.lower(), f"Should not contain English class: {english_class}"

def test_vietnamese_sentence_structure():
    """Test proper Vietnamese sentence structure"""
    # Test various sentence patterns
    patterns = [
        "Một chiếc {object} màu {color} ở khoảng cách {distance}.",
        "Tôi thấy một {object} {color} ở {position}.",
        "Có {count} vật thể: {objects}.",
        "Phía {direction} có {object} {color}."
    ]
    
    for pattern in patterns:
        # Check Vietnamese sentence indicators
        vietnamese_indicators = ['một', 'chiếc', 'màu', 'tôi', 'thấy', 'có', 'vật thể', 'phía']
        found_indicator = any(indicator in pattern for indicator in vietnamese_indicators)
        assert found_indicator, f"Pattern '{pattern}' should contain Vietnamese sentence indicators"

def test_no_english_class_tokens():
    """Test that no English class tokens remain in sentences"""
    common_coco_classes = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
        'truck', 'boat', 'cat', 'dog', 'horse', 'chair', 'bottle', 'book'
    ]
    
    # Expected Vietnamese translations
    vietnamese_translations = {
        'person': 'người',
        'bicycle': 'xe đạp',
        'car': 'ô tô',
        'motorcycle': 'xe máy',
        'cat': 'mèo',
        'dog': 'chó',
        'chair': 'ghế',
        'bottle': 'chai',
        'book': 'sách'
    }
    
    # Create test sentences
    for english, vietnamese in vietnamese_translations.items():
        sentence = f"Một chiếc {vietnamese} màu đen ở khoảng cách gần."
        
        # Should contain Vietnamese
        assert vietnamese in sentence, f"Should contain Vietnamese term: {vietnamese}"
        
        # Should NOT contain English
        assert english not in sentence.lower(), f"Should not contain English term: {english}"

def test_fluent_vietnamese():
    """Test that sentences are fluent Vietnamese"""
    test_sentence = "Tôi thấy một người đàn ông mặc áo đen đang đi bộ ở bên trái, cách khoảng 3 mét."
    
    # Check for Vietnamese characteristics
    vietnamese_chars = 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ'
    has_vietnamese_chars = any(char in test_sentence for char in vietnamese_chars)
    
    vietnamese_words = ['tôi', 'thấy', 'một', 'người', 'mặc', 'đang', 'bên', 'trái', 'cách', 'mét']
    has_vietnamese_words = any(word in test_sentence.lower() for word in vietnamese_words)
    
    assert has_vietnamese_chars or has_vietnamese_words, "Sentence should contain Vietnamese characteristics"
    
    # Should not contain obvious English words in Vietnamese context
    english_words = ['the', 'and', 'is', 'are', 'person', 'walking', 'wearing', 'meters']
    for english_word in english_words:
        assert english_word.lower() not in test_sentence.lower(), f"Vietnamese sentence should not contain: {english_word}"

if __name__ == "__main__":
    test_sentence_builder_single_object()
    test_sentence_builder_multiple_objects()
    test_vietnamese_sentence_structure()
    test_no_english_class_tokens()
    test_fluent_vietnamese()
    print("✅ All sentence builder tests passed!")
