# app/cam_probe.py
import cv2
import logging

logger = logging.getLogger("app.cam_probe")

# Backend priorities and FourCC options
BACKENDS = [cv2.CAP_DSHOW, cv2.CAP_MSMF, 0]   # DSHOW, MSMF, AUTO
FOURCCS = ["MJPG", "YUY2", None]

def try_open(idx, width=640, height=480, fps=30):
    """
    Try to open a camera with different backends and FourCC combinations.
    Returns (success, backend, fourcc) on first working combination.
    """
    for be in BACKENDS:
        cap = cv2.VideoCapture(idx, be) if be else cv2.VideoCapture(idx)
        if not cap or not cap.isOpened():
            if cap:
                cap.release()
            continue
            
        for code in FOURCCS:
            try:
                if code:
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*code))
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                cap.set(cv2.CAP_PROP_FPS, fps)
                
                # Test if we can actually read a frame
                ok, frame = cap.read()
                if ok and frame is not None:
                    cap.release()
                    backend_name = {
                        cv2.CAP_DSHOW: "DSHOW",
                        cv2.CAP_MSMF: "MSMF",
                        0: "AUTO"
                    }.get(be, f"BACKEND_{be}")
                    return True, backend_name, code
            except Exception as e:
                logger.debug(f"Failed to configure idx={idx}, backend={be}, fourcc={code}: {e}")
                continue
        
        cap.release()
    
    return False, None, None

def probe_indices(max_idx=6, width=640, height=480, fps=30):
    """
    Probe camera indices 0 to max_idx-1 and return working configurations.
    Returns list of dicts with index, ok, backend, fourcc info.
    """
    results = []
    logger.info(f"Probing camera indices 0-{max_idx-1}...")
    
    for i in range(max_idx):
        try:
            ok, backend, fourcc = try_open(i, width, height, fps)
            result = {
                "index": i,
                "ok": ok,
                "backend": backend,
                "fourcc": fourcc,
                "config": f"{width}x{height}@{fps}fps"
            }
            results.append(result)
            
            if ok:
                logger.info(f"✅ Camera {i}: {backend}/{fourcc} @ {width}x{height}")
            else:
                logger.debug(f"❌ Camera {i}: not available")
                
        except Exception as e:
            logger.warning(f"Error probing camera {i}: {e}")
            results.append({
                "index": i,
                "ok": False,
                "backend": None,
                "fourcc": None,
                "config": "Error",
                "error": str(e)
            })
    
    working_count = sum(1 for r in results if r["ok"])
    logger.info(f"Camera probe complete: {working_count}/{max_idx} cameras available")
    
    return results

def get_working_cameras(max_idx=6):
    """
    Get only the working camera configurations.
    Returns list of working camera dicts.
    """
    all_results = probe_indices(max_idx)
    working = [r for r in all_results if r["ok"]]
    return working

def format_camera_option(cam_result):
    """
    Format camera result for display in selectbox.
    """
    if not cam_result["ok"]:
        return f"Camera {cam_result['index']} (Not available)"
    
    backend = cam_result["backend"] or "AUTO"
    fourcc = cam_result["fourcc"] or "None"
    return f"Camera {cam_result['index']} ({backend}/{fourcc})"
