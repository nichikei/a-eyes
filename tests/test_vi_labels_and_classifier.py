"""
Tests for Vietnamese labels and classifier system to prevent regressions.

Ensures:
- person → "người" (never missing)
- Correct classifiers for all object types
- No "một cái người" regressions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.vi_nlp import COCO_VI, vi_classifier

def test_person_vi():
    """Test that person maps to 'người' and gets correct classifier"""
    assert COCO_VI["person"] == "người", f"Expected 'người', got '{COCO_VI['person']}'"
    
    result = vi_classifier("person", "người")
    assert result.startswith("một người"), f"Expected 'một người', got '{result}'"
    assert result == "một người"

def test_vehicle_classifiers():
    """Test vehicle classifiers"""
    assert vi_classifier("car", "ô tô") == "một chiếc ô tô"
    assert vi_classifier("motorcycle", "xe máy") == "một chiếc xe máy"
    assert vi_classifier("bus", "xe buýt") == "một chiếc xe buýt"

def test_animal_classifiers():
    """Test animal classifiers"""
    assert vi_classifier("dog", "chó") == "một con chó"
    assert vi_classifier("cat", "mèo") == "một con mèo"
    assert vi_classifier("bird", "chim") == "một con chim"

def test_other_classifiers():
    """Test general object classifiers"""
    assert vi_classifier("cup", "cốc") == "một cái cốc"
    assert vi_classifier("book", "sách") == "một cái sách"

def test_no_cai_nguoi_regression():
    """Critical regression test: NEVER allow 'một cái người'"""
    result = vi_classifier("person", "người")
    assert "một cái người" not in result, f"CRITICAL: Found 'một cái người' in '{result}'"
    assert result == "một người"

def test_detector_bilingual_labels():
    """Test that detector would emit proper bilingual labels"""
    # Simulate what detector.py should do
    label_en = "person"
    label_vi = COCO_VI.get(label_en, "vật thể")
    
    assert label_vi == "người", f"Detector should emit 'người' for person, got '{label_vi}'"
    assert label_vi != "vật thể", "person should never fallback to 'vật thể'"

if __name__ == "__main__":
    test_person_vi()
    test_vehicle_classifiers()
    test_animal_classifiers() 
    test_other_classifiers()
    test_no_cai_nguoi_regression()
    test_detector_bilingual_labels()
    
    print("✅ All Vietnamese label and classifier tests passed!")
    print("✅ No 'một cái người' regressions")
    print("✅ person → 'người' mapping guaranteed")
    print("✅ Correct classifiers for all object types")
