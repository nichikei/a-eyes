from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from collections import Counter

# --- ƯU TIÊN CHỌN CHỦ THỂ CHÍNH ---
MAIN_PRIOR = ["person","bicycle","motorbike","car","dog","cat","chair","sofa","tv"]

# --- NGƯỠNG LỌC NHIỄU NHỎ XÍU (tỉ lệ diện tích so với khung hình) ---
MIN_AREA_RATIO = 0.003  # < 0.3% khung hình coi như nhiễu

# --- TỪ ĐIỂN NHÃN EN->VI (mở rộng khi cần) ---
LABEL_VI = {
    "person": "người",
    "bicycle": "xe đạp",
    "motorbike": "xe máy",
    "motorcycle": "xe máy",
    "car": "ô tô",
    "truck": "xe tải",
    "bus": "xe buýt",
    "train": "tàu hỏa",
    "boat": "thuyền",
    "airplane": "máy bay",
    "dog": "chó",
    "cat": "mèo",
    "bird": "chim",
    "horse": "ngựa",
    "cow": "bò",
    "elephant": "voi",
    "bear": "gấu",
    "zebra": "ngựa vằn",
    "giraffe": "hươu cao cổ",
    "chair": "ghế",
    "sofa": "ghế sofa",
    "couch": "ghế sofa",
    "bed": "giường",
    "dining table": "bàn ăn",
    "table": "bàn",
    "desk": "bàn làm việc",
    "toilet": "nhà vệ sinh",
    "tv": "tivi",
    "television": "tivi",
    "laptop": "máy tính xách tay",
    "computer": "máy tính",
    "mouse": "chuột máy tính",
    "remote": "điều khiển",
    "keyboard": "bàn phím",
    "cell phone": "điện thoại",
    "phone": "điện thoại",
    "microwave": "lò vi sóng",
    "oven": "lò nướng",
    "refrigerator": "tủ lạnh",
    "book": "sách",
    "clock": "đồng hồ",
    "vase": "lọ hoa",
    "scissors": "kéo",
    "teddy bear": "gấu bông",
    "hair drier": "máy sấy tóc",
    "toothbrush": "bàn chải đánh răng",
    "potted plant": "chậu cây",
    "potted_plant": "chậu cây",
    "suitcase": "vali",
    "handbag": "túi xách",
    "backpack": "ba lô",
    "umbrella": "ô",
    "tie": "cà vạt",
    "baseball bat": "gậy bóng chày",
    "baseball glove": "găng tay bóng chày",
    "skateboard": "ván trượt",
    "surfboard": "ván lướt sóng",
    "tennis racket": "vợt tennis",
    "bottle": "chai",
    "wine glass": "ly rượu vang",
    "cup": "cốc",
    "bowl": "tô",
    "banana": "chuối",
    "apple": "táo",
    "orange": "cam",
    "carrot": "cà rốt",
    "pizza": "pizza",
    "donut": "bánh donut",
    "cake": "bánh ngọt",
    "stop sign": "biển báo dừng",
    "parking meter": "đồng hồ đỗ xe",
    "bench": "ghế băng",
    "fire hydrant": "vòi nước cứu hỏa",
}

try:
    # Full 80-class COCO mapping; LABEL_VI above only overrides wording.
    from app.vi_nlp import COCO_VI as _COCO_VI
except Exception:  # pragma: no cover - app package unavailable
    _COCO_VI = {}


def vi_label(en: str) -> str:
    """English COCO label -> Vietnamese. Never returns an English class name
    for a known COCO class (the TTS would read it with a Vietnamese voice)."""
    en = (en or "").lower().strip()
    if not en:
        return "vật thể"
    return LABEL_VI.get(en) or _COCO_VI.get(en) or en

def _clamp(v, lo, hi): 
    return max(lo, min(hi, v))

# ---------------------------
# Chuẩn hóa BBox về xyxy + metadata
# ---------------------------
def normalize_bbox(det: Dict, W: int, H: int) -> Dict:
    """
    Trả về dict: x1,y1,x2,y2,w,h,cx,cy,area,area_ratio,label,conf
    Hỗ trợ các kiểu bbox: "bbox" (xyxy) | "bbox_xywh" | "bbox_cxcywh"
    + fallback các key phổ biến khác (x1,y1,x2,y2) | (x,y,w,h)
    """
    label = (det.get("label") or det.get("name") or "").lower().strip()
    conf  = float(det.get("conf", det.get("confidence", 0.0)))

    if "bbox" in det and len(det["bbox"]) == 4:
        x1,y1,x2,y2 = det["bbox"]
    elif "bbox_xywh" in det and len(det["bbox_xywh"]) == 4:
        x,y,w,h = det["bbox_xywh"]; 
        x1,y1,x2,y2 = x, y, x+w, y+h
    elif "bbox_cxcywh" in det and len(det["bbox_cxcywh"]) == 4:
        cx,cy,w,h = det["bbox_cxcywh"]; 
        x1,y1,x2,y2 = cx-w/2, cy-h/2, cx+w/2, cy+h/2
    else:
        if all(k in det for k in ("x1","y1","x2","y2")):
            x1,y1,x2,y2 = det["x1"],det["y1"],det["x2"],det["y2"]
        elif all(k in det for k in ("x","y","w","h")):
            x1,y1,x2,y2 = det["x"],det["y"],det["x"]+det["w"],det["y"]+det["h"]
        else:
            return {}

    # sửa trường hợp đảo trục
    if x1 > x2: x1,x2 = x2,x1
    if y1 > y2: y1,y2 = y2,y1

    # ép vào biên ảnh
    x1 = _clamp(float(x1), 0, W-1); y1 = _clamp(float(y1), 0, H-1)
    x2 = _clamp(float(x2), 0, W-1); y2 = _clamp(float(y2), 0, H-1)

    w = max(1.0, x2-x1); h = max(1.0, y2-y1)
    cx = x1 + w/2;        cy = y1 + h/2
    area = w*h;           area_ratio = area/float(W*H)

    return {"x1":x1,"y1":y1,"x2":x2,"y2":y2,"w":w,"h":h,
            "cx":cx,"cy":cy,"area":area,"area_ratio":area_ratio,
            "label":label,"conf":conf}

# ---------------------------
# Vị trí kiểu mặt đồng hồ
# ---------------------------
# A forward-facing camera only sees what is in front of the user, so the
# direction comes from the horizontal position alone: the frame width is split
# into five equal sectors read as 10, 11, 12, 1 and 2 o'clock. (The previous
# version took the angle around the frame centre, which reported the top of
# the frame as "6 o'clock, behind you" and a centred object as "3 o'clock".)
_CLOCK_SECTORS = [10, 11, 12, 1, 2]

_CLOCK_TEXT = {
    10: "10 giờ (lệch trái)",
    11: "11 giờ (hơi lệch trái)",
    12: "12 giờ (thẳng phía trước)",
    1: "1 giờ (hơi lệch phải)",
    2: "2 giờ (lệch phải)",
}


def _clock_index(cx: float, cy: float, W: int, H: int) -> int:
    """Clock hour (10, 11, 12, 1 or 2) for an object centred at ``cx``.

    ``cy``/``H`` are accepted for API compatibility; height in the frame says
    nothing about left/right direction.
    """
    r = _clamp(cx / max(1.0, float(W)), 0.0, 0.999999)
    return _CLOCK_SECTORS[int(r * len(_CLOCK_SECTORS))]


def clock_pos(cx: float, cy: float, W: int, H: int) -> str:
    return _CLOCK_TEXT[_clock_index(cx, cy, W, H)]

# ---------------------------
# Cỡ / khoảng cách cảm nhận
# ---------------------------

def size_adj(area_ratio: float) -> str:
    if area_ratio >= 0.18: return "rất lớn"
    if area_ratio >= 0.10: return "lớn"
    if area_ratio >= 0.05: return "vừa"
    return "nhỏ"

def estimate_distance_meters(area_ratio: float, label: str) -> str:
    """
    Ước tính khoảng cách thực tế dựa trên diện tích và loại đối tượng
    """
    # Ước tính dựa trên kích thước thực tế của đối tượng
    if label == "person":
        # Người trung bình cao 1.7m, rộng 0.5m khi đứng thẳng
        if area_ratio >= 0.15: return "dưới 2 mét"
        if area_ratio >= 0.08: return "khoảng 3-4 mét" 
        if area_ratio >= 0.04: return "khoảng 5-7 mét"
        if area_ratio >= 0.02: return "khoảng 8-12 mét"
        return "hơn 15 mét"
    
    elif label in ["car", "ô tô"]:
        # Ô tô trung bình dài 4-5m
        if area_ratio >= 0.20: return "rất gần - cẩn thận"
        if area_ratio >= 0.10: return "khoảng 5-8 mét"
        if area_ratio >= 0.05: return "khoảng 10-15 mét"
        return "hơn 20 mét"
    
    elif label in ["chair", "ghế", "table", "bàn"]:
        # Đồ nội thất
        if area_ratio >= 0.12: return "dưới 2 mét"
        if area_ratio >= 0.06: return "khoảng 2-4 mét"
        if area_ratio >= 0.03: return "khoảng 4-6 mét"
        return "hơn 6 mét"
    
    else:
        # Đối tượng chung
        if area_ratio >= 0.15: return "rất gần"
        if area_ratio >= 0.08: return "khoảng 2-4 mét"
        if area_ratio >= 0.04: return "khoảng 4-8 mét"
        if area_ratio >= 0.02: return "khoảng 8-15 mét"
        return "xa hơn 15 mét"


def range_text(area_ratio: float) -> str:
    # thang 5 mức, dùng trong câu TTS
    if area_ratio >= 0.20: return "rất gần"
    if area_ratio >= 0.10: return "khá gần"
    if area_ratio >= 0.05: return "trung bình"
    if area_ratio >= 0.02: return "hơi xa"
    return "xa"


# ---------------------------
# HỆ THỐNG CẢI THIỆN CHẤT LƯỢNG CÂU TỪ
# ---------------------------

def group_similar_objects(objs: List[Dict]) -> List[List[Dict]]:
    """
    Nhóm các đối tượng cùng loại để tránh lặp từ
    """
    groups = {}
    for obj in objs:
        label = obj["label"]
        if label not in groups:
            groups[label] = []
        groups[label].append(obj)
    
    # Sắp xếp nhóm theo độ quan trọng (diện tích lớn nhất của nhóm)
    sorted_groups = sorted(groups.values(), 
                          key=lambda group: max(obj["area_ratio"] for obj in group), 
                          reverse=True)
    return sorted_groups

def get_urgent_safety_warning(objs: List[Dict], W: int, H: int) -> str:
    """
    Trả về cảnh báo an toàn khẩn cấp nếu có nguy hiểm thực sự
    """
    dangerous_objects = []
    
    for obj in objs:
        # Chỉ cảnh báo khi đối tượng thực sự nguy hiểm và rất gần
        if obj["area_ratio"] > 0.25:  # Rất gần (< 1.5m)
            if obj["label"] in ["car", "truck", "bus"]:
                dangerous_objects.append((obj, "xe lớn"))
            elif obj["label"] in ["motorcycle", "bicycle"] and obj["area_ratio"] > 0.35:
                dangerous_objects.append((obj, "xe nhỏ"))
    
    if dangerous_objects:
        obj, vehicle_type = dangerous_objects[0]  # Lấy đối tượng nguy hiểm nhất
        direction = clock_pos(obj["cx"], obj["cy"], W, H)
        return f"NGUY HIỂM: {vehicle_type} đang rất gần ở {direction}"
    
    return ""

def describe_main_object_smart(group: List[Dict], W: int, H: int) -> str:
    """
    Mô tả nhóm đối tượng chính một cách thông minh và rõ ràng
    """
    if len(group) == 1:
        obj = group[0]
        vi_name = vi_label(obj["label"])
        direction = clock_pos(obj["cx"], obj["cy"], W, H)
        distance = estimate_distance_meters(obj["area_ratio"], obj["label"])
        return f"Có {vi_name} ở vị trí {direction}, {distance}"
    else:
        # Nhiều đối tượng cùng loại
        main_obj = max(group, key=lambda x: x["area_ratio"])
        vi_name = vi_label(main_obj["label"])
        count = len(group)
        direction = clock_pos(main_obj["cx"], main_obj["cy"], W, H)
        distance = estimate_distance_meters(main_obj["area_ratio"], main_obj["label"])
        
        if count == 2:
            return f"Có 2 {vi_name}, trong đó một ở gần bạn hơn tại vị trí {direction}, {distance}"
        else:
            return f"Có {count} {vi_name}, trong đó một ở gần bạn nhất tại vị trí {direction}, {distance}"

def describe_secondary_objects(group: List[Dict], W: int, H: int) -> str:
    """
    Mô tả nhóm đối tượng phụ một cách ngắn gọn và rõ ràng
    """
    if not group:
        return ""
        
    main_obj = max(group, key=lambda x: x["area_ratio"])
    vi_name = vi_label(main_obj["label"])
    direction = clock_pos(main_obj["cx"], main_obj["cy"], W, H)
    
    if len(group) == 1:
        distance = estimate_distance_meters(main_obj["area_ratio"], main_obj["label"])
        return f"Cũng có {vi_name} ở {direction}, {distance}"
    else:
        return f"Còn có {len(group)} {vi_name} ở khu vực {direction}"

def get_smart_navigation_guidance(objs: List[Dict], W: int, H: int) -> str:
    """
    Đưa ra hướng dẫn di chuyển thông minh dựa trên toàn bộ cảnh
    """
    if not objs:
        return "Đường đi phía trước thoáng đãng"
    
    # Phân tích mật độ đối tượng theo hướng
    left_density = len([obj for obj in objs if obj["cx"] < W * 0.4])
    center_density = len([obj for obj in objs if W * 0.4 <= obj["cx"] <= W * 0.6])
    right_density = len([obj for obj in objs if obj["cx"] > W * 0.6])
    
    # Kiểm tra chướng ngại vật lớn
    large_obstacles = [obj for obj in objs if obj["area_ratio"] > 0.2]
    
    if not large_obstacles:
        return "Đường đi tương đối thoáng, có thể tiến thẳng"
    
    # Tìm hướng an toàn nhất
    if left_density <= right_density and left_density <= center_density:
        return "Nên đi về phía bên trái để tránh chướng ngại vật"
    elif right_density <= center_density:
        return "Nên đi về phía bên phải để tránh chướng ngại vật"
    else:
        return "Cẩn thận di chuyển, có nhiều vật cản xung quanh"

def create_natural_sentence(parts: List[str]) -> str:
    """
    Ghép các phần mô tả thành câu tự nhiên, mạch lạc
    """
    if not parts:
        return "Khung hình trống."
    
    # Loại bỏ các phần trống
    valid_parts = [part.strip() for part in parts if part.strip()]
    
    if len(valid_parts) == 1:
        return valid_parts[0] + "."
    
    # Phân loại các phần để ghép tự nhiên
    warnings = []
    descriptions = []
    guidances = []
    
    for part in valid_parts:
        if part.startswith("NGUY HIỂM") or part.startswith("CẢNH BÁO"):
            warnings.append(part)
        elif any(part.startswith(x) for x in ["Nên đi", "Đường đi", "Cẩn thận", "Có nhiều", "Bên"]):
            guidances.append(part)
        else:
            descriptions.append(part)
    
    # Ghép theo thứ tự logic: Cảnh báo -> Mô tả -> Hướng dẫn
    result_parts = warnings + descriptions + guidances
    
    if len(result_parts) == 1:
        return result_parts[0] + "."
    elif len(result_parts) == 2:
        return f"{result_parts[0]}. {result_parts[1]}."
    else:
        # Ghép nhiều phần với từ nối tự nhiên
        result = result_parts[0]
        
        for i, part in enumerate(result_parts[1:], 1):
            if i == len(result_parts) - 1:  # Phần cuối
                result += f". {part}"
            else:
                result += f". {part}"
        
        return result + "."

def improved_heuristic_caption(raw_dets: List[Dict], W: int, H: int) -> str:
    """
    Phiên bản cải tiến của heuristic_caption với câu từ tự nhiên hơn
    """
    # Chuẩn hóa
    objs = [normalize_bbox(d, W, H) for d in raw_dets]
    objs = [o for o in objs if o]  # hợp lệ
    # Lọc nhiễu box quá nhỏ
    objs = [o for o in objs if o["area_ratio"] >= MIN_AREA_RATIO]

    if not objs:
        return "Khung hình trống. Đường đi phía trước có vẻ thông thoáng."

    # Sắp xếp theo diện tích giảm dần
    objs.sort(key=lambda x: -x["area"])

    # Nhóm đối tượng theo loại
    grouped_objects = group_similar_objects(objs)
    
    # Ưu tiên thông tin quan trọng
    result_parts = []
    
    # 1. Cảnh báo an toàn đầu tiên (nếu có)
    urgent_safety = get_urgent_safety_warning(objs, W, H)
    if urgent_safety:
        result_parts.append(urgent_safety)
    
    # 2. Mô tả đối tượng chính
    main_desc = describe_main_object_smart(grouped_objects[0], W, H)
    result_parts.append(main_desc)
    
    # 3. Mô tả các đối tượng khác (tối đa 2 nhóm)
    for group in grouped_objects[1:3]:
        other_desc = describe_secondary_objects(group, W, H)
        if other_desc:
            result_parts.append(other_desc)
    
    # 4. Hướng dẫn di chuyển tổng hợp
    nav_guidance = get_smart_navigation_guidance(objs, W, H)
    if nav_guidance:
        result_parts.append(nav_guidance)

    # Ghép câu một cách tự nhiên
    return create_natural_sentence(result_parts)
