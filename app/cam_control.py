# app/cam_control.py
"""
Safe camera control wrapper to prevent unauthorized stop calls.
Only this module should be used to stop the camera from UI controls.
"""

import inspect
import logging

logger = logging.getLogger("app.cam_control")

def safe_stop(cam, *, reason: str = ""):
    """The only official way to stop the camera from UI controls."""
    caller = inspect.stack()[1]
    logger.warning(
        "Safe camera stop requested by %s:%d %s",
        caller.filename, caller.lineno, f"| reason={reason}" if reason else ""
    )
    cam.stop(_allow=True)
