# app/ui_render.py
import cv2
import time
from typing import Literal, Optional
import numpy as np
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

def to_rgb(frame_bgr: np.ndarray) -> np.ndarray:
    """Convert OpenCV BGR frame to RGB format for Streamlit display."""
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

def render_frame(placeholder: DeltaGenerator, frame_bgr: np.ndarray, *,
                 width: Literal["stretch","content"]="stretch") -> None:
    """
    Safely render a BGR frame to Streamlit using in-memory RGB arrays only.
    
    Args:
        placeholder: Streamlit placeholder element
        frame_bgr: OpenCV BGR image array
        width: Size setting - 'stretch' (full width) or 'content' (natural size)
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return
    
    try:
        # Clear any existing content first to prevent race conditions
        placeholder.empty()
        time.sleep(0.001)  # Small delay to prevent MediaFileStorageError race conditions
        
        rgb = to_rgb(frame_bgr)
        # In-memory render — NO file paths, NO markdown links
        placeholder.image(rgb, channels="RGB", width=width)
    except Exception as e:
        # Log error and clear placeholder on any failure
        import logging
        logger = logging.getLogger("app.ui_render")
        logger.warning(f"Render frame error: {e}")
        clear_placeholder(placeholder)

def clear_placeholder(placeholder: DeltaGenerator) -> None:
    """Clear image placeholder to avoid stale media IDs."""
    try:
        placeholder.empty()
    except Exception:
        pass

def create_placeholder_image(width: int = 640, height: int = 480, 
                           text: str = "Camera Off", 
                           color: tuple = (128, 128, 128)) -> np.ndarray:
    """
    Create a placeholder image with text overlay (returns BGR format).
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        text: Text to display on placeholder
        color: BGR color tuple for background
        
    Returns:
        BGR image array ready for render_frame()
    """
    # Create BGR placeholder image
    placeholder_bgr = np.full((height, width, 3), color, dtype=np.uint8)
    
    # Add text overlay if specified
    if text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        
        # Center the text
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        
        cv2.putText(placeholder_bgr, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
    
    return placeholder_bgr
