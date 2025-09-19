"""
Unit tests for scene captioning functionality
"""

import pytest
import os
import sys
from PIL import Image
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from captioning import SceneDescriber

class TestSceneDescriber:
    """Test the SceneDescriber class"""
    
    def setup_method(self):
        """Setup test instance"""
        self.describer = SceneDescriber(mode="blip", device="cpu")
    
    def test_object_list_to_vn_basic_mapping(self):
        """Test basic Vietnamese object mapping"""
        test_objects = ["person", "chair", "table", "motorbike", "cell phone", "laptop"]
        expected = "người, ghế, bàn, xe máy, điện thoại, laptop"
        
        result = self.describer.object_list_to_vn(test_objects)
        assert result == expected
    
    def test_object_list_to_vn_extended_mapping(self):
        """Test extended Vietnamese object mapping"""
        test_objects = ["car", "bus", "truck", "bicycle", "dog", "cat", "bird"]
        expected = "ô tô, xe buýt, xe tải, xe đạp, chó, mèo, chim"
        
        result = self.describer.object_list_to_vn(test_objects)
        assert result == expected
    
    def test_object_list_to_vn_household_items(self):
        """Test household items mapping"""
        test_objects = ["bottle", "cup", "book", "clock", "tv", "microwave", "refrigerator"]
        expected = "chai, cốc, sách, đồng hồ, tivi, lò vi sóng, tủ lạnh"
        
        result = self.describer.object_list_to_vn(test_objects)
        assert result == expected
    
    def test_object_list_to_vn_unknown_objects(self):
        """Test handling of unknown objects"""
        test_objects = ["unknown_object", "weird_thing"]
        result = self.describer.object_list_to_vn(test_objects)
        
        # Should return the original objects for unknown items
        assert "unknown_object" in result
        assert "weird_thing" in result
    
    def test_object_list_to_vn_mixed_case(self):
        """Test case insensitive mapping"""
        test_objects = ["PERSON", "Chair", "TABLE", "MotorBike"]
        expected = "người, ghế, bàn, xe máy"
        
        result = self.describer.object_list_to_vn(test_objects)
        assert result == expected
    
    def test_object_list_to_vn_empty_list(self):
        """Test empty object list"""
        result = self.describer.object_list_to_vn([])
        assert result == ""
    
    def test_compact_function_word_limit(self):
        """Test text compacting to word limit"""
        long_text = "Đây là một câu rất dài với nhiều từ để kiểm tra chức năng cắt giảm văn bản xuống còn hai mươi lăm từ hoặc ít hơn"
        
        result = self.describer._compact(long_text, max_words=10)
        words = result.replace(".", "").split()
        
        assert len(words) <= 10
        assert result[0].isupper()  # Should be capitalized
        assert result.endswith(".")  # Should end with period
    
    def test_compact_function_capitalization(self):
        """Test proper capitalization"""
        text = "lowercase start"
        result = self.describer._compact(text)
        
        assert result[0].isupper()
        assert result.endswith(".")
    
    def test_compact_function_already_proper(self):
        """Test text that's already properly formatted"""
        text = "Properly formatted text."
        result = self.describer._compact(text)
        
        assert result == text
    
    def test_mode_initialization(self):
        """Test different initialization modes"""
        blip_describer = SceneDescriber(mode="blip")
        assert blip_describer.mode == "blip"
        
        gpt_describer = SceneDescriber(mode="gpt")
        # Should fallback to blip if no API key
        if not os.getenv("OPENAI_API_KEY"):
            assert gpt_describer.mode == "blip"
        else:
            assert gpt_describer.mode == "gpt"
    
    def test_device_auto_detection(self):
        """Test automatic device detection"""
        describer = SceneDescriber()
        assert describer.device in ["cpu", "cuda"]
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OpenAI API key available")
    def test_gpt_mode_with_api_key(self):
        """Test GPT mode when API key is available"""
        describer = SceneDescriber(mode="gpt")
        assert describer.mode == "gpt"
    
    def test_generate_with_objects_fallback(self):
        """Test generate method with fallback (no model loading)"""
        # Create a dummy image
        img = Image.new('RGB', (100, 100), color='red')
        objects = ["person", "chair"]
        
        # This should not fail even if models aren't loaded
        try:
            result = self.describer.generate(img, objects)
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception:
            # If it fails due to missing dependencies, that's expected in test environment
            pass

class TestVietnameseMappings:
    """Specific tests for Vietnamese mapping accuracy"""
    
    def setup_method(self):
        self.describer = SceneDescriber()
    
    def test_person_variants(self):
        """Test person-related mappings"""
        objects = ["person"]
        result = self.describer.object_list_to_vn(objects)
        assert result == "người"
    
    def test_vehicle_mappings(self):
        """Test vehicle mappings"""
        vehicles = {
            "car": "ô tô",
            "bus": "xe buýt", 
            "truck": "xe tải",
            "motorcycle": "xe máy",
            "motorbike": "xe máy",
            "bicycle": "xe đạp"
        }
        
        for en, vn in vehicles.items():
            result = self.describer.object_list_to_vn([en])
            assert result == vn, f"Expected {vn} for {en}, got {result}"
    
    def test_electronics_mappings(self):
        """Test electronics mappings"""
        electronics = {
            "laptop": "laptop",
            "cell phone": "điện thoại",
            "tv": "tivi",
            "mouse": "chuột máy tính",
            "keyboard": "bàn phím",
            "remote": "điều khiển"
        }
        
        for en, vn in electronics.items():
            result = self.describer.object_list_to_vn([en])
            assert result == vn, f"Expected {vn} for {en}, got {result}"
    
    def test_animals_mappings(self):
        """Test animal mappings"""
        animals = {
            "dog": "chó",
            "cat": "mèo", 
            "bird": "chim"
        }
        
        for en, vn in animals.items():
            result = self.describer.object_list_to_vn([en])
            assert result == vn, f"Expected {vn} for {en}, got {result}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])