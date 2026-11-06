"""Tests for the Vietnamese caption pipeline that /api/describe actually uses."""

import pytest

from app.vi_nlp import COCO_VI
from captioning_heuristic import (
    clock_pos,
    estimate_distance_meters,
    improved_heuristic_caption,
    normalize_bbox,
    range_text,
    size_adj,
    vi_label,
)

W, H = 640, 480

# The 80 class names of the COCO-pretrained YOLO weights the backend loads.
COCO_80 = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
]


def det(label, x1, y1, x2, y2, conf=0.9):
    return {"label": label, "bbox": [x1, y1, x2, y2], "confidence": conf}


# --------------------------------------------------------------- labels


def test_coco_mapping_covers_all_80_classes():
    assert len(COCO_80) == 80
    assert set(COCO_80) <= set(COCO_VI)


# Class names whose Vietnamese word is spelled the same (loanwords).
SAME_IN_VI = {"pizza", "laptop"}


@pytest.mark.parametrize("en", COCO_80)
def test_every_coco_class_gets_a_vietnamese_label(en):
    vi = vi_label(en)
    assert vi
    if en not in SAME_IN_VI:
        # Regression: 'traffic light', 'sports ball', 'fork'... used to be read
        # out in English by the Vietnamese voice.
        assert vi != en, f"{en!r} has no Vietnamese label"


def test_vi_label_is_case_and_whitespace_insensitive():
    assert vi_label("  Person ") == "người"
    assert vi_label("") == "vật thể"


# ------------------------------------------------------------ direction


@pytest.mark.parametrize(
    "cx, hour",
    [(10, "10 giờ"), (190, "11 giờ"), (320, "12 giờ"), (450, "1 giờ"), (630, "2 giờ")],
)
def test_clock_direction_follows_horizontal_position(cx, hour):
    assert clock_pos(cx, 240, W, H).startswith(hour + " ")


@pytest.mark.parametrize("cy", [0, 120, 240, 360, 479])
def test_centred_object_is_straight_ahead_at_any_height(cy):
    # Regression: the old angle-around-centre formula said "3 giờ" for the
    # exact centre and "6 giờ (phía sau)" for the top of the frame.
    assert clock_pos(320, cy, W, H).startswith("12 giờ")


def test_clock_never_points_behind_the_user():
    hours = {clock_pos(x, y, W, H).split()[0] for x in range(0, W, 16) for y in range(0, H, 16)}
    assert hours == {"10", "11", "12", "1", "2"}


# ------------------------------------------------------- size & distance


def test_normalize_bbox_computes_centre_and_area_ratio():
    nb = normalize_bbox(det("person", 100, 50, 300, 470), W, H)
    assert (nb["cx"], nb["cy"]) == (200.0, 260.0)
    assert nb["area_ratio"] == pytest.approx(200 * 420 / (W * H))


def test_size_and_range_buckets_are_monotonic():
    ratios = [0.5, 0.2, 0.1, 0.05, 0.02, 0.005]
    sizes = [size_adj(r) for r in ratios]
    ranges = [range_text(r) for r in ratios]
    assert sizes[0] == "rất lớn" and sizes[-1] == "nhỏ"
    assert ranges[0] == "rất gần" and ranges[-1] == "xa"


def test_person_distance_estimate_gets_closer_as_box_grows():
    assert estimate_distance_meters(0.30, "person") == "dưới 2 mét"
    assert estimate_distance_meters(0.10, "person") == "khoảng 3-4 mét"
    assert estimate_distance_meters(0.005, "person") == "hơn 15 mét"


# -------------------------------------------------------------- caption


def test_empty_frame_caption():
    assert improved_heuristic_caption([], W, H).startswith("Khung hình trống")


def test_caption_names_object_direction_and_distance_in_vietnamese():
    cap = improved_heuristic_caption([det("person", 260, 40, 380, 470)], W, H)
    assert "người" in cap
    assert "12 giờ" in cap
    assert "mét" in cap
    assert "person" not in cap


def test_caption_warns_about_close_vehicle_first():
    cap = improved_heuristic_caption([det("car", 420, 120, 640, 480)], W, H)
    assert cap.split(".")[0].upper().startswith(("NGUY HIỂM", "CẢNH BÁO", "CẨN THẬN"))
    assert "ô tô" in cap


def test_tiny_boxes_are_ignored_as_noise():
    # 4x4 px = 0.005% of the frame, below MIN_AREA_RATIO.
    assert improved_heuristic_caption([det("cup", 10, 10, 14, 14)], W, H).startswith("Khung hình trống")
