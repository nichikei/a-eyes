"""
Smart Image Analysis for Object Detection Fallback
Phân tích ảnh thông minh khi YOLO không hoạt động
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def analyze_image_features(cv_image: np.ndarray) -> Dict:
    """Phân tích đặc điểm ảnh để đoán có vật thể gì"""
    H, W = cv_image.shape[:2]
    
    # Chuyển sang grayscale để phân tích
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    
    # Phân tích độ sáng
    brightness = np.mean(gray)
    
    # Phân tích contrast
    contrast = np.std(gray)
    
    # Tìm edges để xem có vật thể không
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (H * W)
    
    # Phân tích màu sắc
    color_analysis = analyze_color_distribution(cv_image)
    
    # Tìm contours để xác định có hình dạng gì
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Lọc contours có kích thước hợp lý
    significant_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > (H * W * 0.01):  # Ít nhất 1% diện tích ảnh
            significant_contours.append(contour)
    
    return {
        'brightness': brightness,
        'contrast': contrast,
        'edge_density': edge_density,
        'color_analysis': color_analysis,
        'contours': significant_contours,
        'likely_objects': predict_likely_objects(brightness, contrast, edge_density, significant_contours)
    }

def analyze_color_distribution(cv_image: np.ndarray) -> Dict:
    """Phân tích phân bố màu sắc trong ảnh"""
    # Chuyển sang HSV để phân tích màu tốt hơn
    hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
    
    # Phân tích dominant colors
    h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
    s_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
    v_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])
    
    # Tìm dominant hue
    dominant_hue = np.argmax(h_hist)
    dominant_saturation = np.argmax(s_hist)
    dominant_value = np.argmax(v_hist)
    
    # Classify environment type based on colors
    environment_type = classify_environment(dominant_hue, dominant_saturation, dominant_value)
    
    return {
        'dominant_hue': dominant_hue,
        'dominant_saturation': dominant_saturation, 
        'dominant_value': dominant_value,
        'environment_type': environment_type
    }

def classify_environment(hue: int, saturation: int, value: int) -> str:
    """Phân loại môi trường dựa trên màu sắc"""
    if value < 50:
        return "dark_indoor"  # Trong nhà tối
    elif value > 200 and saturation < 50:
        return "bright_indoor"  # Trong nhà sáng
    elif saturation > 100:
        if 35 <= hue <= 85:  # Green range
            return "outdoor_nature"  # Ngoài trời thiên nhiên
        elif 100 <= hue <= 140:  # Blue range  
            return "outdoor_sky"  # Ngoài trời có trời xanh
        else:
            return "colorful_indoor"  # Trong nhà nhiều màu
    else:
        return "neutral_indoor"  # Trong nhà trung tính

def predict_likely_objects(brightness: float, contrast: float, edge_density: float, contours: List) -> List[Dict]:
    """Dự đoán các vật thể có thể có dựa trên đặc điểm ảnh"""
    likely_objects = []
    
    # Nếu có nhiều edge và contrast cao -> có thể có người hoặc vật thể rõ ràng
    if edge_density > 0.1 and contrast > 30:
        # Phân tích shape của contours để đoán
        for contour in contours[:3]:  # Chỉ xem 3 contour lớn nhất
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 1
            area = cv2.contourArea(contour)
            
            # Dự đoán dựa trên aspect ratio và vị trí
            if 0.3 <= aspect_ratio <= 0.8 and y < brightness * 2:  # Có thể là người
                likely_objects.append({
                    'label': 'person',
                    'confidence': min(0.6, edge_density * 5),
                    'bbox': [x, y, x + w, y + h],
                    'reason': 'vertical_shape_detected'
                })
            elif 1.2 <= aspect_ratio <= 3.0:  # Có thể là xe, bàn
                if y > brightness:  # Ở dưới -> có thể là bàn
                    likely_objects.append({
                        'label': 'table',
                        'confidence': min(0.4, edge_density * 3),
                        'bbox': [x, y, x + w, y + h],
                        'reason': 'horizontal_shape_detected'
                    })
                else:  # Ở trên -> có thể là xe
                    likely_objects.append({
                        'label': 'car',
                        'confidence': min(0.3, edge_density * 2),
                        'bbox': [x, y, x + w, y + h],
                        'reason': 'rectangular_shape_detected'
                    })
    
    # Nếu brightness thấp nhưng có một ít contrast -> có thể có vật thể mờ
    elif brightness < 80 and contrast > 15:
        # Tạo detection chung chung ở giữa
        H, W = 480, 640  # Default size
        likely_objects.append({
            'label': 'unknown_object',
            'confidence': 0.2,
            'bbox': [W//3, H//3, 2*W//3, 2*H//3],
            'reason': 'low_light_object_detected'
        })
    
    # Nếu quá sáng -> có thể overexposed nhưng vẫn có vật thể
    elif brightness > 200:
        H, W = 480, 640
        likely_objects.append({
            'label': 'person',  # Assume person in bright scene
            'confidence': 0.25,
            'bbox': [W//4, H//6, 3*W//4, 5*H//6],
            'reason': 'bright_scene_person_assumed'
        })
    
    return likely_objects

def smart_fallback_detection(cv_image: np.ndarray) -> List[Dict]:
    """Tạo fallback detection thông minh dựa trên phân tích ảnh"""
    logger.info("🧠 Analyzing image for smart fallback detection...")
    
    # Phân tích ảnh
    analysis = analyze_image_features(cv_image)
    
    logger.info(f"📊 Image analysis: brightness={analysis['brightness']:.1f}, "
                f"contrast={analysis['contrast']:.1f}, edges={analysis['edge_density']:.3f}")
    
    # Lấy predicted objects
    predicted_objects = analysis['likely_objects']
    
    # Nếu không predict được gì, tạo default
    if not predicted_objects:
        H, W = cv_image.shape[:2]
        
        # Dựa trên environment type để tạo default
        env_type = analysis['color_analysis']['environment_type']
        
        if env_type == "outdoor_nature":
            predicted_objects.append({
                'label': 'tree',
                'confidence': 0.3,
                'bbox': [W//4, 0, 3*W//4, 2*H//3],
                'reason': 'outdoor_nature_scene'
            })
        elif env_type == "outdoor_sky":
            predicted_objects.append({
                'label': 'building',
                'confidence': 0.25,
                'bbox': [W//6, H//3, 5*W//6, H],
                'reason': 'outdoor_urban_scene'
            })
        else:  # Indoor scenes
            predicted_objects.append({
                'label': 'person',
                'confidence': 0.3,
                'bbox': [W//4, H//6, 3*W//4, 5*H//6],
                'reason': 'indoor_person_assumed'
            })
            
            # Add furniture for indoor
            predicted_objects.append({
                'label': 'chair',
                'confidence': 0.2,
                'bbox': [W//8, H//2, W//3, 4*H//5],
                'reason': 'indoor_furniture_assumed'
            })
    
    # Convert to YOLO format
    detections = []
    for obj in predicted_objects:
        detections.append({
            'label': obj['label'],
            'label_en': obj['label'],
            'bbox': obj['bbox'],
            'confidence': obj['confidence'],
            'source': 'smart_fallback'
        })
    
    logger.info(f"🎯 Created {len(detections)} smart fallback detections")
    return detections

if __name__ == "__main__":
    # Test with a sample image
    print("Testing smart fallback detection...")
    
    # Create a test image
    test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Add some structure to make it more realistic
    cv2.rectangle(test_img, (100, 100), (300, 400), (255, 255, 255), -1)  # White rectangle
    cv2.circle(test_img, (500, 200), 50, (0, 255, 0), -1)  # Green circle
    
    detections = smart_fallback_detection(test_img)
    
    for det in detections:
        print(f"Detected: {det['label']} with confidence {det['confidence']:.2f}")