# app/media_guard.py
import re
import pathlib
import logging
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

logger = logging.getLogger("app.media_guard")

def install_media_guard(strict: bool = True):
    """
    Runtime guard to block path-based image calls and force in-memory rendering.
    
    If strict=True: raise on any path-based image/markdown so we get a traceback
    If strict=False: log + no-op instead of crashing (useful in prod)
    """
    
    # Wrap st.image
    _orig_st_image = st.image
    def _st_image_wrapped(image, *args, **kwargs):
        if isinstance(image, (str, pathlib.Path)):
            msg = f"Path-based st.image blocked: {image}"
            if strict:
                raise RuntimeError(msg)
            logger.error(msg)
            return  # swallow the call
        return _orig_st_image(image, *args, **kwargs)
    st.image = _st_image_wrapped

    # Wrap DeltaGenerator.image (placeholders, columns, etc.)
    _orig_dg_image = DeltaGenerator.image
    def _dg_image_wrapped(self, image=None, *args, **kwargs):
        if isinstance(image, (str, pathlib.Path)):
            msg = f"Path-based DeltaGenerator.image blocked: {image}"
            if strict:
                raise RuntimeError(msg)
            logger.error(msg)
            return
        return _orig_dg_image(self, image, *args, **kwargs)
    DeltaGenerator.image = _dg_image_wrapped

    # Wrap st.markdown to prevent markdown image paths
    _orig_markdown = st.markdown
    IMG_MD = re.compile(r"!\[[^\]]*\]\((?!data:)[^)]+\.(?:jpg|jpeg|png|gif)\)", re.IGNORECASE)
    def _markdown_wrapped(body, *args, **kwargs):
        if isinstance(body, str) and IMG_MD.search(body):
            msg = "Markdown image with file path blocked (use in-memory arrays instead)"
            if strict:
                raise RuntimeError(msg + f": {body[:120]}...")
            logger.error(msg)
            # Strip the offending image markdown
            safe = IMG_MD.sub("[image blocked]", body)
            return _orig_markdown(safe, *args, **kwargs)
        return _orig_markdown(body, *args, **kwargs)
    st.markdown = _markdown_wrapped

    # Wrap st.sidebar.image as well
    if hasattr(st.sidebar, 'image'):
        _orig_sidebar_image = st.sidebar.image
        def _sidebar_image_wrapped(image, *args, **kwargs):
            if isinstance(image, (str, pathlib.Path)):
                msg = f"Path-based st.sidebar.image blocked: {image}"
                if strict:
                    raise RuntimeError(msg)
                logger.error(msg)
                return
            return _orig_sidebar_image(image, *args, **kwargs)
        st.sidebar.image = _sidebar_image_wrapped

    logger.info("🛡️ MEDIA GUARD installed (strict=%s)", strict)

def is_path_like(obj) -> bool:
    """Check if an object looks like a file path."""
    if isinstance(obj, (str, pathlib.Path)):
        str_obj = str(obj)
        # Check for file extensions
        if re.search(r'\.(jpg|jpeg|png|gif|bmp|tiff|webp)$', str_obj, re.IGNORECASE):
            return True
        # Check for relative/absolute paths without extensions
        if '/' in str_obj or '\\' in str_obj:
            return True
    return False

def check_for_path_violations(frame_locals: dict) -> None:
    """Debug helper to check local variables for potential path violations."""
    violations = []
    for name, value in frame_locals.items():
        if is_path_like(value):
            violations.append(f"{name}={value}")
    
    if violations:
        logger.warning("Potential path violations in frame: %s", ", ".join(violations))
