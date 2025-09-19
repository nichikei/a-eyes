"""
Runtime diagnostics module for PyTorch environment validation and device management.
Ensures PyTorch is loaded from project venv and provides safe device selection.
"""

import sys
import os
import logging
from typing import Dict, Any, Optional


def assert_torch_from_venv(strict: bool = True) -> None:
    """
    Verify that PyTorch is loaded from the project virtual environment.
    
    Args:
        strict: If True (default), raise RuntimeError on mismatch. If False, log warning.
        
    Raises:
        RuntimeError: If torch is not from venv and strict=True
    """
    try:
        import torch
    except ImportError:
        raise RuntimeError("PyTorch is not installed")
    
    # Get paths
    torch_path = os.path.abspath(torch.__file__)
    exe = os.path.abspath(sys.executable)
    
    # Determine venv root (executable is in venv/Scripts/python.exe or venv/bin/python)
    venv_root = os.path.abspath(os.path.join(exe, "..", ".."))
    
    # Normalize Windows paths for comparison
    if os.name == 'nt':
        torch_path = torch_path.replace("\\", "/")
        venv_root = venv_root.replace("\\", "/")
    
    # Check if torch is under venv
    try:
        common_path = os.path.commonpath([venv_root, torch_path])
        # Normalize for comparison
        if os.name == 'nt':
            common_path = common_path.replace("\\", "/")
        
        is_in_venv = common_path == venv_root
    except ValueError:
        # Different drives on Windows
        is_in_venv = False
    
    if not is_in_venv:
        error_msg = f"🚨 PyTorch is not from this venv!\n  Torch: {torch_path}\n  Venv: {venv_root}\n  Executable: {exe}"
        if strict:
            raise RuntimeError(error_msg)
        else:
            logging.warning(f"⚠️ {error_msg}")


def pick_device() -> str:
    """
    Select appropriate device based on CAPTION_DEVICE environment variable.
    
    Returns:
        Device string: "cpu" or "cuda"
    """
    import torch
    
    device_env = os.getenv("CAPTION_DEVICE", "auto").lower()
    
    if device_env == "cpu":
        # Force CPU mode
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        return "cpu"
    elif device_env == "cuda":
        # Prefer CUDA but fallback to CPU if not available
        if torch.cuda.is_available():
            return "cuda"
        else:
            logging.warning("🔧 CUDA requested but not available, falling back to CPU")
            return "cpu"
    elif device_env == "auto":
        # Auto-detect
        if torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    else:
        logging.warning(f"🔧 Unknown CAPTION_DEVICE '{device_env}', using auto")
        return "cuda" if torch.cuda.is_available() else "cpu"


def log_torch_env(logger: logging.Logger) -> Dict[str, Any]:
    """
    Log PyTorch environment information and return as dict.
    
    Args:
        logger: Logger instance to use
        
    Returns:
        Dictionary with environment information
    """
    import torch
    
    # Collect environment info
    exe = sys.executable
    torch_file = torch.__file__
    torch_version = torch.__version__
    cuda_available = torch.cuda.is_available()
    torch_cuda_version = torch.version.cuda if hasattr(torch.version, 'cuda') else None
    device_from_env = os.getenv("CAPTION_DEVICE", "auto")
    strict_venv = os.getenv("STRICT_VENV_TORCH", "1")
    
    # Log with emojis
    logger.info(f"🔧 Python executable: {exe}")
    logger.info(f"📦 PyTorch file: {torch_file}")
    logger.info(f"⚙️ PyTorch version: {torch_version}")
    logger.info(f"🖥️ CUDA available: {cuda_available}")
    logger.info(f"🔌 CUDA version: {torch_cuda_version}")
    logger.info(f"🎛️ CAPTION_DEVICE: {device_from_env}")
    logger.info(f"🔒 STRICT_VENV_TORCH: {strict_venv}")
    
    return {
        "exe": exe,
        "torch_file": torch_file,
        "torch_version": torch_version,
        "cuda_available": cuda_available,
        "torch_cuda_version": torch_cuda_version,
        "device_from_env": device_from_env,
        "strict_venv": strict_venv
    }


def diag_snapshot(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a diagnostic snapshot with environment and runtime information.
    
    Args:
        extra: Additional fields to include in the snapshot
        
    Returns:
        Complete diagnostic dictionary
    """
    try:
        import torch
        
        # Base diagnostic info
        base_info = {
            "exe": sys.executable,
            "torch_file": torch.__file__,
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "torch_cuda_version": getattr(torch.version, 'cuda', None),
            "device_from_env": os.getenv("CAPTION_DEVICE", "auto"),
            "strict_venv": os.getenv("STRICT_VENV_TORCH", "1"),
            "python_version": sys.version,
            "platform": sys.platform,
            "torch_import_success": True
        }
    except ImportError as e:
        # Torch not available
        base_info = {
            "exe": sys.executable,
            "torch_file": "NOT_AVAILABLE",
            "torch_version": "NOT_AVAILABLE", 
            "cuda_available": False,
            "torch_cuda_version": None,
            "device_from_env": os.getenv("CAPTION_DEVICE", "auto"),
            "strict_venv": os.getenv("STRICT_VENV_TORCH", "1"),
            "python_version": sys.version,
            "platform": sys.platform,
            "torch_import_success": False,
            "torch_import_error": str(e)
        }
    except Exception as e:
        # Torch import fails (e.g., missing DLL)
        base_info = {
            "exe": sys.executable,
            "torch_file": "IMPORT_FAILED",
            "torch_version": "IMPORT_FAILED",
            "cuda_available": False,
            "torch_cuda_version": None,
            "device_from_env": os.getenv("CAPTION_DEVICE", "auto"),
            "strict_venv": os.getenv("STRICT_VENV_TORCH", "1"),
            "python_version": sys.version,
            "platform": sys.platform,
            "torch_import_success": False,
            "torch_import_error": str(e)
        }
    
    # Merge with extra fields if provided
    if extra:
        base_info.update(extra)
    
    return base_info


def validate_venv_torch() -> bool:
    """
    Validate that torch is from venv, respecting STRICT_VENV_TORCH env var.
    
    Returns:
        True if validation passes or is non-strict, False otherwise
    """
    try:
        strict = os.getenv("STRICT_VENV_TORCH", "1") != "0"
        assert_torch_from_venv(strict=strict)
        return True
    except RuntimeError:
        return False