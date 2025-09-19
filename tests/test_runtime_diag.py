"""
Tests for runtime_diag module to verify venv checking and device selection functionality.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import logging

# Import the module to test
from runtime_diag import (
    assert_torch_from_venv, 
    pick_device, 
    log_torch_env, 
    diag_snapshot,
    validate_venv_torch
)


class TestAssertTorchFromVenv:
    """Test venv validation functionality"""
    
    def test_torch_in_venv_strict_mode(self):
        """Test that torch in venv passes strict validation"""
        with patch('sys.executable', '/path/to/venv/Scripts/python.exe'), \
             patch('torch.__file__', '/path/to/venv/Lib/site-packages/torch/__init__.py'), \
             patch('os.path.commonpath') as mock_commonpath:
            
            # Mock commonpath to return venv root (indicating torch is in venv)
            mock_commonpath.return_value = '/path/to/venv'
            
            # Should not raise
            assert_torch_from_venv(strict=True)
    
    def test_torch_outside_venv_strict_mode(self):
        """Test that torch outside venv raises error in strict mode"""
        with patch('sys.executable', '/path/to/venv/Scripts/python.exe'), \
             patch('torch.__file__', '/usr/lib/python3.11/site-packages/torch/__init__.py'), \
             patch('os.path.commonpath') as mock_commonpath:
            
            # Mock commonpath to return different path (indicating torch is outside venv)
            mock_commonpath.return_value = '/usr/lib'
            
            with pytest.raises(RuntimeError, match="PyTorch is not from this venv"):
                assert_torch_from_venv(strict=True)
    
    def test_torch_outside_venv_non_strict_mode(self, caplog):
        """Test that torch outside venv logs warning in non-strict mode"""
        with patch('sys.executable', '/path/to/venv/Scripts/python.exe'), \
             patch('torch.__file__', '/usr/lib/python3.11/site-packages/torch/__init__.py'), \
             patch('os.path.commonpath') as mock_commonpath:
            
            # Mock commonpath to return different path
            mock_commonpath.return_value = '/usr/lib'
            
            with caplog.at_level(logging.WARNING):
                assert_torch_from_venv(strict=False)
                
            assert "PyTorch is not from this venv" in caplog.text
    
    def test_windows_path_normalization(self):
        """Test Windows path normalization"""
        with patch('sys.executable', r'C:\vision\.venv\Scripts\python.exe'), \
             patch('torch.__file__', r'C:\vision\.venv\Lib\site-packages\torch\__init__.py'), \
             patch('os.name', 'nt'), \
             patch('os.path.commonpath') as mock_commonpath:
            
            # Mock commonpath to return venv root
            mock_commonpath.return_value = 'C:/vision/.venv'
            
            # Should not raise
            assert_torch_from_venv(strict=True)
    
    def test_different_drives_windows(self):
        """Test different drives on Windows (should fail)"""
        with patch('sys.executable', r'C:\vision\.venv\Scripts\python.exe'), \
             patch('torch.__file__', r'D:\torch\__init__.py'), \
             patch('os.name', 'nt'), \
             patch('os.path.commonpath', side_effect=ValueError("Different drives")):
            
            with pytest.raises(RuntimeError, match="PyTorch is not from this venv"):
                assert_torch_from_venv(strict=True)


class TestPickDevice:
    """Test device selection functionality"""
    
    def test_pick_device_cpu_explicit(self):
        """Test explicit CPU device selection"""
        with patch.dict(os.environ, {'CAPTION_DEVICE': 'cpu'}):
            device = pick_device()
            assert device == "cpu"
            assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    
    def test_pick_device_cuda_available(self):
        """Test CUDA device selection when available"""
        with patch.dict(os.environ, {'CAPTION_DEVICE': 'cuda'}), \
             patch('torch.cuda.is_available', return_value=True):
            
            device = pick_device()
            assert device == "cuda"
    
    def test_pick_device_cuda_unavailable(self, caplog):
        """Test CUDA device fallback when unavailable"""
        with patch.dict(os.environ, {'CAPTION_DEVICE': 'cuda'}), \
             patch('torch.cuda.is_available', return_value=False):
            
            with caplog.at_level(logging.WARNING):
                device = pick_device()
                
            assert device == "cpu"
            assert "CUDA requested but not available" in caplog.text
    
    def test_pick_device_auto_cuda_available(self):
        """Test auto device selection with CUDA available"""
        with patch.dict(os.environ, {'CAPTION_DEVICE': 'auto'}), \
             patch('torch.cuda.is_available', return_value=True):
            
            device = pick_device()
            assert device == "cuda"
    
    def test_pick_device_auto_cpu_only(self):
        """Test auto device selection with CPU only"""
        with patch.dict(os.environ, {'CAPTION_DEVICE': 'auto'}), \
             patch('torch.cuda.is_available', return_value=False):
            
            device = pick_device()
            assert device == "cpu"
    
    def test_pick_device_default_auto(self):
        """Test default device selection (auto mode)"""
        with patch.dict(os.environ, {}, clear=True), \
             patch('torch.cuda.is_available', return_value=False):
            
            device = pick_device()
            assert device == "cpu"
    
    def test_pick_device_unknown_mode(self, caplog):
        """Test unknown device mode falls back to auto"""
        with patch.dict(os.environ, {'CAPTION_DEVICE': 'unknown'}), \
             patch('torch.cuda.is_available', return_value=False):
            
            with caplog.at_level(logging.WARNING):
                device = pick_device()
                
            assert device == "cpu"
            assert "Unknown CAPTION_DEVICE" in caplog.text


class TestLogTorchEnv:
    """Test environment logging functionality"""
    
    def test_log_torch_env(self, caplog):
        """Test torch environment logging"""
        mock_logger = MagicMock()
        
        with patch('sys.executable', '/path/to/python'), \
             patch('torch.__file__', '/path/to/torch/__init__.py'), \
             patch('torch.__version__', '2.0.0'), \
             patch('torch.cuda.is_available', return_value=True), \
             patch('torch.version.cuda', '11.8'), \
             patch.dict(os.environ, {'CAPTION_DEVICE': 'auto', 'STRICT_VENV_TORCH': '1'}):
            
            result = log_torch_env(mock_logger)
            
            # Check that logger was called
            assert mock_logger.info.call_count >= 5
            
            # Check returned dict
            assert result['exe'] == '/path/to/python'
            assert result['torch_file'] == '/path/to/torch/__init__.py'
            assert result['torch_version'] == '2.0.0'
            assert result['cuda_available'] is True
            assert result['torch_cuda_version'] == '11.8'
            assert result['device_from_env'] == 'auto'
            assert result['strict_venv'] == '1'


class TestDiagSnapshot:
    """Test diagnostic snapshot functionality"""
    
    def test_diag_snapshot_basic(self):
        """Test basic diagnostic snapshot"""
        with patch('sys.executable', '/path/to/python'), \
             patch('torch.__file__', '/path/to/torch/__init__.py'), \
             patch('torch.__version__', '2.0.0'), \
             patch('torch.cuda.is_available', return_value=False), \
             patch('torch.version.cuda', None):
            
            result = diag_snapshot()
            
            assert 'exe' in result
            assert 'torch_file' in result
            assert 'torch_version' in result
            assert 'cuda_available' in result
            assert 'python_version' in result
            assert 'platform' in result
    
    def test_diag_snapshot_with_extra(self):
        """Test diagnostic snapshot with extra fields"""
        extra_fields = {
            'device': 'cpu',
            'model_ready': True,
            'custom_field': 'test_value'
        }
        
        with patch('sys.executable', '/path/to/python'), \
             patch('torch.__file__', '/path/to/torch/__init__.py'), \
             patch('torch.__version__', '2.0.0'), \
             patch('torch.cuda.is_available', return_value=False):
            
            result = diag_snapshot(extra=extra_fields)
            
            # Check that extra fields are included
            for key, value in extra_fields.items():
                assert result[key] == value
            
            # Check that base fields are still there
            assert 'exe' in result
            assert 'torch_version' in result


class TestValidateVenvTorch:
    """Test venv validation with environment variable control"""
    
    def test_validate_venv_torch_strict_success(self):
        """Test successful validation in strict mode"""
        with patch.dict(os.environ, {'STRICT_VENV_TORCH': '1'}), \
             patch('runtime_diag.assert_torch_from_venv') as mock_assert:
            
            result = validate_venv_torch()
            
            assert result is True
            mock_assert.assert_called_once_with(strict=True)
    
    def test_validate_venv_torch_strict_failure(self):
        """Test validation failure in strict mode"""
        with patch.dict(os.environ, {'STRICT_VENV_TORCH': '1'}), \
             patch('runtime_diag.assert_torch_from_venv', side_effect=RuntimeError("Torch not in venv")):
            
            result = validate_venv_torch()
            
            assert result is False
    
    def test_validate_venv_torch_non_strict(self):
        """Test validation in non-strict mode"""
        with patch.dict(os.environ, {'STRICT_VENV_TORCH': '0'}), \
             patch('runtime_diag.assert_torch_from_venv') as mock_assert:
            
            result = validate_venv_torch()
            
            assert result is True
            mock_assert.assert_called_once_with(strict=False)