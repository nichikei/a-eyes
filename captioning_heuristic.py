from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from collections import Counter
import math

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

def vi_label(en: str) -> str:
    en = (en or "").lower().strip()
    return LABEL_VI.get(en, en if en else "vật thể")

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
# Vị trí trái-phải / trên-dưới (dạng cũ)
# ---------------------------
def lr_pos(cx: float, W: int) -> str:
    r = cx / max(1.0, W)
    if r < 0.33: return "bên trái"
    if r > 0.67: return "bên phải"
    return "giữa"

def tb_pos(cy: float, H: int) -> str:
    r = cy / max(1.0, H)
    if r < 0.33: return "phía trên"
    if r > 0.67: return "phía dưới"
    return "chính giữa"

# ---------------------------
# Vị trí kiểu mặt đồng hồ (12 cung 30°)
# ---------------------------
def _clock_index(cx: float, cy: float, W: int, H: int) -> int:
    """
    Gán hướng theo 12 cung. 12 giờ = phía trên, 3 giờ = bên phải, 6 giờ = phía dưới, 9 giờ = bên trái.
    Từ góc nhìn của người mù (không flip horizontal vì đã xử lý ở camera)
    """
    # Không flip horizontal - sử dụng tọa độ gốc
    dx = cx - W / 2.0
    dy = (H / 2.0) - cy  # trục y hướng lên
    
    # Tính góc từ center, với 12 giờ là 0 độ
    ang = (math.degrees(math.atan2(dy, dx)) + 360.0 + 90.0) % 360.0
    idx = int(round(ang / 30.0)) % 12
    
    return idx

def clock_pos(cx: float, cy: float, W: int, H: int) -> str:
    idx = _clock_index(cx, cy, W, H)
    # Sử dụng cách diễn đạt tự nhiên hơn
    positions = [
        "12 giờ (thẳng phía trước)",
        "1 giờ (hơi lệch phải)",
        "2 giờ (lệch phải)",
        "3 giờ (bên phải)",
        "4 giờ (lệch phải phía sau)",
        "5 giờ (hơi lệch phải phía sau)",
        "6 giờ (phía sau)",
        "7 giờ (hơi lệch trái phía sau)",
        "8 giờ (lệch trái phía sau)",
        "9 giờ (bên trái)",
        "10 giờ (lệch trái)",
        "11 giờ (hơi lệch trái)"
    ]
    return positions[idx]

# ---------------------------
# Cỡ / khoảng cách cảm nhận
# ---------------------------
def near_far(area_ratio: float) -> Optional[str]:
    # (giữ lại cho tương thích) — dùng range_text ở dưới để nhất quán hơn
    if area_ratio >= 0.12: return "khá gần"
    if area_ratio <= 0.03: return "xa"
    return None

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

def describe_relative_position(objs: List[Dict]) -> str:
    """
    Mô tả vị trí tương đối giữa các đối tượng để người mù hiểu không gian
    """
    if len(objs) < 2:
        return ""
    
    descriptions = []
    
    # Tìm người nếu có
    people = [o for o in objs if o["label"] == "person"]
    others = [o for o in objs if o["label"] != "person"]
    
    if people and others:
        person = max(people, key=lambda x: x["area"])
        
        for obj in others[:2]:  # Chỉ mô tả 2 vật gần nhất
            # So sánh vị trí
            p_clock = _clock_index(person["cx"], person["cy"], 1280, 720)  # Giả sử resolution
            o_clock = _clock_index(obj["cx"], obj["cy"], 1280, 720)
            
            # Tính relative position
            diff = (o_clock - p_clock) % 12
            
            if diff <= 2 or diff >= 10:
                relation = "gần"
            elif 3 <= diff <= 5:
                relation = "bên phải"
            elif 6 <= diff <= 8:
                relation = "phía sau"
            else:
                relation = "bên trái"
            
            descriptions.append(f"{vi_label(obj['label'])} ở {relation} người")
    
    # Mô tả nhóm đối tượng
    elif len(objs) >= 3:
        # Tìm cluster objects
        left_objs = [o for o in objs if o["cx"] < 640]  # Bên trái màn hình
        right_objs = [o for o in objs if o["cx"] >= 640]  # Bên phải màn hình
        
        if len(left_objs) >= 2:
            descriptions.append(f"có {len(left_objs)} vật thể ở bên trái")
        if len(right_objs) >= 2:
            descriptions.append(f"có {len(right_objs)} vật thể ở bên phải")
    
    return ". ".join(descriptions)

def navigation_guidance(objs: List[Dict]) -> str:
    """
    Đưa ra hướng dẫn di chuyển cho người mù
    """
    if not objs:
        return "Đường đi phía trước có vẻ thông thoáng"
    
    guidance = []
    
    # Kiểm tra đường đi phía trước (11-1 giờ)
    front_objs = []
    for obj in objs:
        clock_idx = _clock_index(obj["cx"], obj["cy"], 1280, 720)
        if clock_idx in [11, 0, 1] and obj["area_ratio"] >= 0.05:  # Đối tượng lớn ở phía trước
            front_objs.append(obj)
    
    if front_objs:
        largest = max(front_objs, key=lambda x: x["area"])
        guidance.append(f"Chú ý: {vi_label(largest['label'])} chắn đường phía trước")
        
        # Gợi ý hướng tránh
        left_clear = not any(_clock_index(o["cx"], o["cy"], 1280, 720) in [9, 10] 
                           for o in objs if o["area_ratio"] >= 0.05)
        right_clear = not any(_clock_index(o["cx"], o["cy"], 1280, 720) in [2, 3] 
                            for o in objs if o["area_ratio"] >= 0.05)
        
        if left_clear and right_clear:
            guidance.append("có thể đi bên trái hoặc bên phải")
        elif left_clear:
            guidance.append("nên đi bên trái")
        elif right_clear:
            guidance.append("nên đi bên phải")
        else:
            guidance.append("cần cẩn thận, nhiều vật cản xung quanh")
    
    return ". ".join(guidance)

def safety_warning(label: str, area_ratio: float, clock_pos: str) -> str:
    """
    Cảnh báo an toàn cho người mù
    """
    warnings = []
    
    # Cảnh báo xe cộ gần
    if label in ["car", "ô tô", "truck", "xe tải", "bus", "xe buýt"] and area_ratio >= 0.08:
        warnings.append("CẨN THẬN: xe cộ đang gần")
    
    # Cảnh báo người đang di chuyển về phía trước
    if label == "person" and area_ratio >= 0.12 and "12" in clock_pos:
        warnings.append("có người đang ở phía trước")
    
    # Cảnh báo vật cản ở chính giữa đường đi
    if area_ratio >= 0.10 and any(h in clock_pos for h in ["11", "12", "1"]):
        warnings.append(f"chú ý {vi_label(label)} ở phía trước")
    
    return ". ".join(warnings)

def range_text(area_ratio: float) -> str:
    # thang 5 mức, dùng trong câu TTS
    if area_ratio >= 0.20: return "rất gần"
    if area_ratio >= 0.10: return "khá gần"
    if area_ratio >= 0.05: return "trung bình"
    if area_ratio >= 0.02: return "hơi xa"
    return "xa"

def _clock_bucket(cx: float, cy: float, W: int, H: int) -> int:
    # để loại trùng hướng trong câu 2
    return _clock_index(cx, cy, W, H)

# ---------------------------
# Chọn chủ thể chính
# ---------------------------
def choose_main(objs: List[Dict]) -> Optional[Dict]:
    if not objs: 
        return None
    persons = [o for o in objs if o["label"]=="person"]
    if persons:
        return max(persons, key=lambda o: o["area"])
    cand = [o for o in objs if o["label"] in MAIN_PRIOR]
    if cand:
        return max(cand, key=lambda o: o["area"])
    return max(objs, key=lambda o: o["area"])

# ---------------------------
# Câu mô tả 1 vật: an toàn TTS (không dấu phẩy giữa mệnh đề)
# ---------------------------
def describe_one_vi(o: Dict, W: int, H: int) -> str:
    label_vi = vi_label(o["label"])
    clock = clock_pos(o["cx"], o["cy"], W, H)
    size  = size_adj(o["area_ratio"])
    dist  = range_text(o["area_ratio"])
    # Không dùng dấu phẩy, câu ngắn — TTS đọc trọn vẹn
    return f"{label_vi} ở hướng {clock} kích thước {size} khoảng cách {dist}."

# ---------------------------
# Tạo mô tả heuristic (1–3 câu)
# ---------------------------
def heuristic_caption(raw_dets: List[Dict], W: int, H: int) -> str:
    """
    Tạo mô tả chi tiết cho người mù:
    - Mô tả chính với khoảng cách thực tế
    - Cảnh báo an toàn nếu cần
    - Mô tả vị trí tương đối
    - Hướng dẫn di chuyển
    """
    # Chuẩn hóa
    objs = [normalize_bbox(d, W, H) for d in raw_dets]
    objs = [o for o in objs if o]  # hợp lệ
    # Lọc nhiễu box quá nhỏ
    objs = [o for o in objs if o["area_ratio"] >= MIN_AREA_RATIO]

    if not objs:
        return "Khung hình trống."

    # Sắp xếp theo diện tích giảm dần
    objs.sort(key=lambda x: -x["area"])

    # Chủ thể chính
    main = choose_main(objs)
    if not main:
        return "Khung hình trống."

    parts: List[str] = []
    
    # Mô tả chính với khoảng cách chi tiết
    main_desc = describe_one_vi_enhanced(main, W, H)
    parts.append(main_desc)
    
    # Cảnh báo an toàn cho đối tượng chính
    safety = safety_warning(main["label"], main["area_ratio"], 
                           clock_pos(main["cx"], main["cy"], W, H))
    if safety:
        parts.append(safety)

    # Các đối tượng khác: tối đa 2, tránh cùng hướng/nhãn với main
    others = []
    main_bucket = _clock_bucket(main["cx"], main["cy"], W, H)
    for o in objs:
        if o is main:
            continue
        if len(others) >= 2:
            break
        # tránh trùng nhãn và cùng hướng để câu đỡ lặp
        if o["label"] == main["label"]:
            continue
        if _clock_bucket(o["cx"], o["cy"], W, H) == main_bucket:
            continue
        others.append(o)

    for o in others:
        parts.append(describe_one_vi_enhanced(o, W, H))

    # Thêm mô tả vị trí tương đối
    relative_desc = describe_relative_position(objs)
    if relative_desc:
        parts.append(relative_desc)
    
    # Thêm hướng dẫn di chuyển
    nav_guidance = navigation_guidance(objs)
    if nav_guidance:
        parts.append(nav_guidance)

    out = ". ".join(s.strip().rstrip(" ,") for s in parts if s).strip()
    return out or "Khung hình trống."

def describe_one_vi_enhanced(obj: Dict, W: int, H: int) -> str:
    """
    Mô tả chi tiết một đối tượng với thông tin khoảng cách thực tế
    """
    label = obj["label"]
    vi_name = vi_label(label)
    cx, cy = obj["cx"], obj["cy"]
    area_ratio = obj["area_ratio"]
    
    clock = clock_pos(cx, cy, W, H)
    distance = estimate_distance_meters(area_ratio, label)
    
    return f"{vi_name} ở hướng {clock}, {distance}"

# ---------------------------
# (Giữ lại cho tương thích) Vị trí theo trái-phải / trên-dưới
# & helper ghép location kiểu cũ — có thể dùng nơi khác để log
# ---------------------------
def _compose_location(lr: str, tb: str) -> str:
    """
    Tránh 'ở ở giữa': lr_pos trả 'giữa' / 'bên trái' / 'bên phải'
    """
    loc = "ở giữa khung hình" if lr=="giữa" else f"ở {lr} khung hình"
    if tb != "chính giữa": 
        loc += f" {tb}"
    return loc

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

def get_smart_navigation_guidance(objs: List[Dict], W: int, H: int) -> str:
    """
    Đưa ra hướng dẫn di chuyển thông minh và cụ thể
    """
    if not objs:
        return "Đường đi phía trước khá thoáng"
    
    # Phân loại đối tượng theo mức độ nguy hiểm
    obstacles = []
    people = []
    vehicles = []
    
    for obj in objs:
        if obj["label"] in ["car", "truck", "bus", "motorcycle", "bicycle"]:
            vehicles.append(obj)
        elif obj["label"] == "person":
            people.append(obj)
        else:
            obstacles.append(obj)
    
    # Phân tích không gian an toàn
    left_clear = True
    right_clear = True
    front_clear = True
    
    # Kiểm tra từng vùng
    for obj in objs:
        if obj["area_ratio"] > 0.1:  # Đối tượng đủ lớn để cản đường
            cx_ratio = obj["cx"] / W
            cy_ratio = obj["cy"] / H
            
            if cx_ratio < 0.35:  # Bên trái
                left_clear = False
            elif cx_ratio > 0.65:  # Bên phải  
                right_clear = False
            
            if cy_ratio > 0.6:  # Phía trước/dưới
                front_clear = False
    
    # Đưa ra lời khuyên cụ thể
    if vehicles:
        if len(vehicles) > 1:
            return "Cẩn thận: có nhiều xe cộ xung quanh, nên dừng lại và chờ đường thông thoáng hơn"
        else:
            vehicle = vehicles[0]
            cx_ratio = vehicle["cx"] / W
            if cx_ratio < 0.5:
                return "Có xe ở bên trái, nên đi về phía bên phải để an toàn"
            else:
                return "Có xe ở bên phải, nên đi về phía bên trái để an toàn"
    
    if people and len(people) > 2:
        return "Có nhiều người xung quanh, di chuyển chậm và cẩn thận"
    
    # Hướng dẫn di chuyển dựa trên không gian trống
    if front_clear and left_clear and right_clear:
        return "Đường đi tương đối thoáng, có thể tiến thẳng bình thường"
    elif left_clear and not right_clear:
        return "Bên phải có vật cản, nên đi lệch về phía bên trái"
    elif right_clear and not left_clear:
        return "Bên trái có vật cản, nên đi lệch về phía bên phải"
    elif not front_clear:
        return "Phía trước có chướng ngại vật, cần tìm đường đi khác"
    else:
        return "Xung quanh có nhiều vật cản, di chuyển thật cẩn thận"

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
