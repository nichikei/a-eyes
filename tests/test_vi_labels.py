"""
Test Vietnamese label mappings for COCO classes.
Verifies that core object classes have proper Vietnamese translations.
"""
import sys
from pathlib import Path
import pytest

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_vi_mapping_function():
    """Test the Vietnamese mapping function directly"""
    from app.vi_nlp import map_label_en_to_vi
    
    # Test key mappings
    assert map_label_en_to_vi("person") == "người"
    assert map_label_en_to_vi("car") == "ô tô" 
    assert map_label_en_to_vi("bicycle") == "xe đạp"
    assert map_label_en_to_vi("cat") == "mèo"
    assert map_label_en_to_vi("dog") == "chó"


def test_required_vietnamese_mappings():
    """Test that all required Vietnamese mappings exist per specification."""
    from app.vi_nlp import map_label_en_to_vi
    
    # Required mappings as per specification
    required_mappings = {
        "person": "người",
        "car": "ô tô", 
        "bicycle": "xe đạp",
        "motorcycle": "xe máy",
        "bus": "xe buýt",
        "truck": "xe tải",
        "chair": "ghế",
        "bench": "ghế dài"
    }
    
    for english_class, expected_vietnamese in required_mappings.items():
        actual_vietnamese = map_label_en_to_vi(english_class)
        assert actual_vietnamese == expected_vietnamese, f"Mapping for '{english_class}': got '{actual_vietnamese}', expected '{expected_vietnamese}'"
    
    print(f"✅ All {len(required_mappings)} required Vietnamese mappings are correct")


def test_vietnamese_mapping_coverage():
    """Test that Vietnamese mappings have good coverage of COCO classes."""
    try:
        from app.vi_nlp import get_coco_vi_mapping
        coco_vi = get_coco_vi_mapping()
        
        # Should have at least 50 Vietnamese mappings for good coverage
        assert len(coco_vi) >= 50, f"Vietnamese mapping has only {len(coco_vi)} entries, expected at least 50"
        print(f"✅ Vietnamese mapping has good coverage: {len(coco_vi)} classes")
    except ImportError:
        # If function doesn't exist, test individual mappings
        from app.vi_nlp import map_label_en_to_vi
        
        # Test a variety of COCO classes
        test_classes = [
            "person", "car", "bicycle", "motorcycle", "airplane", "bus", "train", "truck",
            "boat", "traffic light", "stop sign", "chair", "sofa", "bed", "dining table",
            "toilet", "tv", "laptop", "mouse", "keyboard", "cell phone", "book", "clock",
            "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"
        ]
        
        mapped_count = 0
        for class_name in test_classes:
            result = map_label_en_to_vi(class_name)
            if result != class_name:  # If it's translated (not just returned as-is)
                mapped_count += 1
        
        # Should map at least 80% of common classes
        coverage_ratio = mapped_count / len(test_classes)
        assert coverage_ratio >= 0.8, f"Only {coverage_ratio:.1%} of test classes are mapped to Vietnamese"
        print(f"✅ Good mapping coverage: {coverage_ratio:.1%} of test classes mapped")


def test_no_english_in_vietnamese_values():
    """Test that Vietnamese translations don't contain English words."""
    from app.vi_nlp import map_label_en_to_vi
    
    # Test classes that should be fully in Vietnamese
    test_classes = ["person", "car", "bicycle", "motorcycle", "bus", "truck", "chair", "bench"]
    
    # Common English words that shouldn't appear in Vietnamese translations
    english_words = ["person", "car", "bike", "bus", "truck", "chair", "table", "the", "a", "an"]
    
    violations = []
    for class_name in test_classes:
        vietnamese_translation = map_label_en_to_vi(class_name)
        for english_word in english_words:
            if english_word.lower() in vietnamese_translation.lower():
                violations.append(f"{class_name} -> '{vietnamese_translation}' contains English word '{english_word}'")
    
    assert not violations, f"Vietnamese translations contain English words: {violations}"
    print(f"✅ All Vietnamese translations are pure Vietnamese (no English words)")


def test_vietnamese_diacritics_present():
    """Test that Vietnamese translations include proper diacritics."""
    from app.vi_nlp import map_label_en_to_vi
    
    # Test classes that should have Vietnamese diacritics
    test_classes = ["car", "motorcycle", "bicycle", "person", "chair"]
    
    # Vietnamese diacritics that should appear in translations
    vietnamese_chars = ['ă', 'â', 'đ', 'ê', 'ô', 'ơ', 'ư', 'á', 'à', 'ả', 'ã', 'ạ']
    
    has_diacritics = False
    for class_name in test_classes:
        vietnamese_translation = map_label_en_to_vi(class_name)
        if any(char in vietnamese_translation for char in vietnamese_chars):
            has_diacritics = True
            break
    
    assert has_diacritics, "Vietnamese translations should include proper diacritics"
    print(f"✅ Vietnamese translations include proper diacritics")
    
    # Test fallback
    assert map_label_en_to_vi("unknown_object") == "vật thể"
    assert map_label_en_to_vi("") == "vật thể"

def test_coco_vi_person():
    """Test that COCO class 'person' maps to Vietnamese 'người'"""
    from app.vi_nlp import COCO_VI
    
    assert 'person' in COCO_VI
    assert COCO_VI['person'] == 'người'

def test_coco_vi_car():
    """Test that COCO class 'car' maps to Vietnamese 'ô tô'"""
    from app.vi_nlp import COCO_VI
    
    assert 'car' in COCO_VI
    assert COCO_VI['car'] == 'ô tô'

def test_coco_vi_complete_mapping():
    """Test that all expected COCO classes have Vietnamese translations"""
    from app.detector import ObjectDetector
    
    detector = ObjectDetector(
        model_name='yolov5s',
        confidence_threshold=0.5,
        language='vi'
    )
    
    # Key COCO classes that should have Vietnamese translations
    expected_mappings = {
        'person': 'người',
        'bicycle': 'xe đạp',
        'car': 'ô tô',
        'motorcycle': 'xe máy',
        'bus': 'xe buýt',
        'cat': 'mèo',
        'dog': 'chó',
        'chair': 'ghế',
        'bottle': 'chai',
        'book': 'sách'
    }
    
    for english, vietnamese in expected_mappings.items():
        assert english in detector.vietnamese_classes, f"Missing mapping for {english}"
        assert detector.vietnamese_classes[english] == vietnamese, f"Wrong mapping for {english}: expected {vietnamese}, got {detector.vietnamese_classes[english]}"

if __name__ == "__main__":
    # Run tests directly if executed as script
    test_coco_vi_person()
    test_coco_vi_car() 
    test_coco_vi_complete_mapping()
    print("✅ All Vietnamese label tests passed!")
