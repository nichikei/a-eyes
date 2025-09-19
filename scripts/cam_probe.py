import cv2
import time

BACKENDS = [
    ("DSHOW", getattr(cv2, "CAP_DSHOW", 700)),
    ("MSMF",  getattr(cv2, "CAP_MSMF", 1400)),
    ("AUTO",  0),
]

FOURCCS = [
    ("MJPG", cv2.VideoWriter_fourcc(*"MJPG")),
    ("YUY2", cv2.VideoWriter_fourcc(*"YUY2")),
    ("NONE", None),
]

SIZES = [(640,480), (1280,720)]
FPS = [30, 60]

def try_combo(index, bname, api, fourcc_name, fourcc, size, fps):
    print(f"Trying idx={index} backend={bname} fourcc={fourcc_name} {size[0]}x{size[1]}@{fps}")
    cap = cv2.VideoCapture(index, api)
    if not cap.isOpened():
        print("  open: FAIL")
        return False
    
    if fourcc is not None:
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    ok_frames = 0
    t0 = time.time()
    while time.time() - t0 < 3.0:
        ok, frame = cap.read()
        if ok and frame is not None:
            ok_frames += 1
            if ok_frames >= 5:
                break
        time.sleep(0.02)
    
    cap.release()
    if ok_frames >= 5:
        print("  ✅ frames: OK")
        return True
    else:
        print("  ❌ frames: NO")
        return False

if __name__ == "__main__":
    index = 0
    good = []
    
    for bname, api in BACKENDS:
        for fourcc_name, fourcc in FOURCCS:
            for size in SIZES:
                for f in FPS:
                    if try_combo(index, bname, api, fourcc_name, fourcc, size, f):
                        good.append((bname, fourcc_name, size, f))
    
    print("\n=== GOOD COMBINATIONS ===")
    for g in good:
        print(g)
