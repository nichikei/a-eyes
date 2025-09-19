"""
Tests for Vietnamese classifier system to prevent regressions.

Ensures correct classifiers are used for different object types:
- People: "một người"
- Animals: "một con"
- Vehicles: "một chiếc"
- Other objects: "một cái"

Also tests sentence normalization.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.vi_nlp import vi_classifier, normalize_vi_sentence

def test_people_classifier():
    """Test that people get 'một người' classifier"""
    result = vi_classifier("person", "người")
    assert result.startswith("một người"), f"Expected 'một người', got '{result}'"
    assert result == "một người"

def test_vehicle_classifier():
    """Test that vehicles get 'một chiếc' classifier"""
    result = vi_classifier("car", "ô tô")
    assert result.startswith("một chiếc"), f"Expected 'một chiếc ô tô', got '{result}'"
    assert result == "một chiếc ô tô"
    
    # Test other vehicles
    assert vi_classifier("motorcycle", "xe máy") == "một chiếc xe máy"
    assert vi_classifier("bus", "xe buýt") == "một chiếc xe buýt"
    assert vi_classifier("bicycle", "xe đạp") == "một chiếc xe đạp"

def test_animal_classifier():
    """Test that animals get 'một con' classifier"""
    result = vi_classifier("dog", "chó")
    assert result.startswith("một con"), f"Expected 'một con chó', got '{result}'"
    assert result == "một con chó"
    
    # Test other animals
    assert vi_classifier("cat", "mèo") == "một con mèo"
    assert vi_classifier("bird", "chim") == "một con chim"
    assert vi_classifier("elephant", "voi") == "một con voi"

def test_other_classifier():
    """Test that other objects get 'một cái' classifier"""
    result = vi_classifier("cup", "cốc")
    assert result.startswith("một cái"), f"Expected 'một cái cốc', got '{result}'"
    assert result == "một cái cốc"
    
    # Test other objects
    assert vi_classifier("book", "sách") == "một cái sách"
    assert vi_classifier("bottle", "chai") == "một cái chai"
    assert vi_classifier("chair", "ghế") == "một cái ghế"

def test_normalize_center():
    """Test that 'bên ở giữa' gets normalized to 'ở giữa'"""
    result = normalize_vi_sentence("Một cái bàn màu nâu ở khoảng cách gần, bên ở giữa")
    assert result.endswith("ở giữa."), f"Expected to end with 'ở giữa.', got '{result}'"
    assert "bên ở giữa" not in result, "Should not contain 'bên ở giữa'"

def test_normalize_double_spaces():
    """Test that double spaces are collapsed"""
    result = normalize_vi_sentence("Một  con  chó  màu  nâu")
    assert "  " not in result, f"Should not contain double spaces, got '{result}'"
    assert result == "Một con chó màu nâu."

def test_normalize_trailing_period():
    """Test that sentences get trailing period"""
    result = normalize_vi_sentence("Một người màu da ở khoảng cách xa")
    assert result.endswith("."), f"Should end with period, got '{result}'"
    assert result == "Một người màu da ở khoảng cách xa."

def test_no_cai_nguoi_regression():
    """Critical test: ensure we never get 'một cái người'"""
    result = vi_classifier("person", "người")
    assert "một cái người" not in result, f"CRITICAL: Found 'một cái người' in '{result}'"
    assert result == "một người"

if __name__ == "__main__":
    # Run all tests
    test_people_classifier()
    test_vehicle_classifier()
    test_animal_classifier()
    test_other_classifier()
    test_normalize_center()
    test_normalize_double_spaces()
    test_normalize_trailing_period()
    test_no_cai_nguoi_regression()
    
    print("✅ All tests passed!")
    print("✅ No 'một cái người' regressions")
    print("✅ Correct classifiers for all object types")
    print("✅ Sentence normalization working correctly")
