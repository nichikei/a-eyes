# 👁️ AI for Blind - Hệ thống AI hỗ trợ người mù

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Tổng quan

**AI for Blind** là hệ thống AI tiên tiến được thiết kế đặc biệt để hỗ trợ người mù và khiếm thị tại Việt Nam. Sử dụng công nghệ thị giác máy tính hiện đại, xử lý ngôn ngữ tự nhiên và tổng hợp giọng nói để cung cấp mô tả môi trường chi tiết bằng tiếng Việt tự nhiên.

Hệ thống phân tích video thời gian thực từ camera, nhận diện đối tượng, ước tính khoảng cách và cung cấp hướng dẫn di chuyển an toàn thông qua giọng nói Việt Nam.

## ✨ Tính năng chính

### 🎯 Nhận diện đối tượng thời gian thực
- **Công nghệ YOLO**: Phát hiện 80+ loại đối tượng (người, xe cộ, đồ vật, v.v.)
- **Tối ưu cho Việt Nam**: Từ điển tiếng Việt hoàn chỉnh với 60+ đối tượng
- **Xử lý real-time**: Phân tích video trực tiếp với tốc độ cao

### 📏 Ước tính khoảng cách thông minh
- **Khoảng cách thực tế**: Ước tính mét dựa trên kích thước đối tượng
- **Mô tả không gian**: "khoảng 3-4 mét", "dưới 2 mét", "rất gần"
- **Định vị chính xác**: Hệ thống tọa độ đồng hồ (12 giờ = phía trước)

### 🧭 Hướng dẫn điều hướng thông minh
- **Phân tích không gian**: Đánh giá các khu vực an toàn để di chuyển
- **Cảnh báo nguy hiểm**: Phát hiện xe cộ, chướng ngại vật gần
- **Lời khuyên di chuyển**: "Nên đi về bên trái", "Cẩn thận phía trước"

### � Tổng hợp giọng nói tiếng Việt
- **TTS chất lượng cao**: Giọng nói tự nhiên, rõ ràng
- **Câu từ mạch lạc**: Tránh lặp từ, mô tả theo thứ tự ưu tiên
- **Phản hồi tức thì**: Mô tả ngay khi phát hiện đối tượng

### 💻 Giao diện web hiện đại
- **React + TypeScript**: Giao diện responsive, chuyên nghiệp
- **Tab thông minh**: Lịch sử giọng nói và Ảnh chụp được tổ chức rõ ràng
- **Accessibility tối ưu**: Thiết kế đặc biệt cho người khiếm thị
## 🏗️ Kiến trúc hệ thống

### Backend (FastAPI)
```
simple_yolo_backend.py
├── Nhận diện đối tượng (YOLO)
├── Hệ thống mô tả thông minh (captioning_heuristic.py)
├── Tổng hợp giọng nói tiếng Việt (tts_vn.py)
├── Phát hiện thông minh (smart_fallback.py)
└── API RESTful với CORS
```

### Frontend (React)
```
web/src/
├── App.tsx (Giao diện chính với tabs)
├── components/
│   ├── Transcript.tsx (Lịch sử giọng nói)
│   ├── Snapshots.tsx (Ảnh chụp)
│   └── CameraView.tsx (Camera real-time)
└── Responsive design với Tailwind CSS
```

### AI Core
```
captioning_heuristic.py
├── Nhóm đối tượng thông minh
├── Ước tính khoảng cách thực tế
├── Cảnh báo an toàn
├── Hướng dẫn điều hướng
└── Template câu tự nhiên
```

## 🚀 Cài đặt và sử dụng

### Yêu cầu hệ thống
- **Python 3.11+**
- **Node.js 18+** (cho frontend)
- **Webcam** hoặc camera USB
- **Speakers/Headphones** cho phản hồi âm thanh
- **Windows 10/11** (đã tối ưu)

### Cài đặt nhanh

1. **Clone repository**
   ```bash
   git clone https://github.com/nichikei/ai-for-blind.git
   cd ai-for-blind
   ```

2. **Thiết lập Python environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Cài đặt frontend**
   ```bash
   cd web
   npm install
   ```

4. **Khởi động hệ thống**
   
   **Bước 1: Kích hoạt virtual environment**
   ```bash
   .venv\Scripts\activate
   ```
   
   **Bước 2: Khởi động Backend (Terminal 1)**
   ```bash
   python simple_yolo_backend.py
   ```
   
   **Bước 3: Khởi động Frontend (Terminal 2 mới)**
   ```bash
   cd web
   npm run dev
   ```

5. **Truy cập ứng dụng**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8011

### Sử dụng cơ bản

1. **Cho phép truy cập camera** khi trình duyệt yêu cầu
2. **Chọn chế độ**:
   - **Auto Mode**: Tự động chụp và mô tả liên tục
   - **Manual Mode**: Nhấn "Take Photo" để chụp thủ công
3. **Nghe mô tả** qua speakers/headphones bằng tiếng Việt
4. **Xem lịch sử** trong tab "Speech History"
5. **Lưu ảnh** trong tab "Snapshots"

### Lưu ý quan trọng
- Đảm bảo **kích hoạt venv** trước khi chạy backend
- **Backend phải chạy trước** frontend
- Sử dụng **2 terminal riêng biệt** cho backend và frontend

## 🎨 Demo và ví dụ

### Ví dụ mô tả trước cải tiến:
```
"Người ở hướng 2 giờ, gần. Xe ở hướng 10 giờ, xa. Cẩn thận di chuyển."
```

### Ví dụ mô tả sau cải tiến:
```
"Có người ở vị trí 2 giờ (hơi lệch phải), khoảng 3-4 mét. 
Cũng có xe ở khu vực 10 giờ (lệch trái). 
Bên phải có vật cản, nên đi lệch về phía bên trái."
```

### Các tính năng nâng cao:
- **Nhóm đối tượng**: "Có 3 người, trong đó một ở gần bạn nhất..."
- **Cảnh báo khẩn cấp**: "NGUY HIỂM: xe lớn đang rất gần ở 12 giờ"
- **Hướng dẫn cụ thể**: "Có xe ở bên trái, nên đi về phía bên phải để an toàn"

## 📁 Cấu trúc dự án

```
ai-for-blind/
├── 📁 web/                          # Frontend React
│   ├── src/
│   │   ├── App.tsx                   # Giao diện chính
│   │   ├── components/
│   │   └── styles/
│   ├── package.json
│   └── vite.config.ts
├── 📄 simple_yolo_backend.py         # FastAPI backend chính
├── 📄 captioning_heuristic.py        # AI mô tả thông minh
├── 📄 tts_vn.py                     # Text-to-Speech tiếng Việt
├── 📄 smart_fallback.py             # Phát hiện dự phòng
├── 📄 model_registry.py             # Quản lý AI models
├── 📄 fallback_detection.py         # Thuật toán dự phòng
├── 📁 tests/                        # Unit tests và integration tests
├── 📄 requirements.txt              # Python dependencies
├── 📄 config.yaml                   # Cấu hình hệ thống
└── 📄 README.md                     # Tài liệu này
```

## ⚙️ Cấu hình nâng cao

### Tùy chỉnh TTS
```python
# config.yaml
tts:
  voice_rate: 200          # Tốc độ nói (words/min)
  voice_volume: 0.9        # Âm lượng (0.0-1.0)
  always_speak: false      # Tự động phát âm
```

### Tùy chỉnh phát hiện
```python
detection:
  confidence_threshold: 0.5    # Ngưỡng tin cậy
  min_area_ratio: 0.01        # Diện tích tối thiểu
  max_objects: 3              # Số đối tượng tối đa mô tả
```

## 🔧 Troubleshooting

### Lỗi thường gặp

**1. Camera không hoạt động**
```bash
# Kiểm tra quyền truy cập camera
# Đảm bảo chỉ có 1 ứng dụng sử dụng camera
```

**2. TTS không phát âm**
```bash
# Kiểm tra audio output
# Cài đặt codec audio Windows
pip install pycaw
```

**3. Backend không khởi động**
```bash
# Kiểm tra port 8011
netstat -an | findstr :8011
taskkill /f /im python.exe
```

**4. Frontend build error**
```bash
# Xóa node_modules và cài lại
rm -rf node_modules package-lock.json
npm install
```

## 🧪 Testing

### Chạy tests
```bash
# Unit tests
python -m pytest tests/ -v

# Integration tests
python test_full_stack.py

# Performance tests
python test_performance_comprehensive.py
```

### Test coverage
```bash
# Kiểm tra coverage
pip install pytest-cov
pytest --cov=. tests/
```

## 🚧 Roadmap

### Phiên bản 2.0 (Q1 2026)
- [ ] **Offline AI**: Chạy hoàn toàn offline
- [ ] **Mobile App**: Ứng dụng iOS/Android
- [ ] **GPS Integration**: Định vị và điều hướng GPS
- [ ] **Voice Commands**: Điều khiển bằng giọng nói

### Phiên bản 2.1 (Q2 2026)
- [ ] **Face Recognition**: Nhận diện khuôn mặt người quen
- [ ] **Text OCR**: Đọc văn bản, biển báo
- [ ] **Currency Detection**: Nhận diện tiền Việt Nam
- [ ] **Indoor Navigation**: Điều hướng trong nhà

### Phiên bản 3.0 (Q3 2026)
- [ ] **AR Integration**: Tích hợp thực tế ảo tăng cường
- [ ] **Multi-language**: Hỗ trợ tiếng Anh, Pháp
- [ ] **Cloud AI**: AI mạnh mẽ hơn trên cloud
- [ ] **Wearable Support**: Hỗ trợ thiết bị đeo

4. **Download VOSK model** (for voice commands)
   ```bash
   # Download Vietnamese VOSK model
   # Instructions will be provided in the voice_commands.py module
   ```

5. **Test camera access**
   ```bash
   python -c "import cv2; print('Camera test:', cv2.VideoCapture(0).isOpened())"
   ```

## 🎯 How to Run

### Start the Application
```bash
streamlit run main.py
```

The application will open in your default web browser at `http://localhost:8501`

### Using the Application

1. **Camera Setup**: Ensure your camera is connected and working
2. **Audio Setup**: Check speakers/headphones and microphone
3. **Start Detection**: Click "Start" to begin real-time analysis
4. **Voice Commands**: Use the microphone for voice control
5. **View Results**: See detections in both visual and text format

### Configuration Options

- **Detection Confidence**: Adjust minimum confidence threshold
- **Language Settings**: Choose between online/offline TTS
- **Voice Commands**: Enable/disable voice control
- **Distance Units**: Switch between relative and metric distances

## 📁 Project Structure

```
ai-eyes/
├── app/
│   ├── detector.py              # YOLOv5 object detection
│   ├── color_recognition.py     # Color analysis module
│   ├── distance_estimation.py   # Distance calculation
│   ├── ocr.py                  # Vietnamese OCR
│   ├── speech.py               # Text-to-speech synthesis
│   ├── voice_commands.py       # Voice command recognition
│   └── processor.py            # Main processing pipeline
├── models/                     # Pre-trained models
├── assets/                     # Static assets
├── tests/                      # Unit tests
├── main.py                     # Streamlit application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔮 Future Improvements

### Enhanced Features
- **GPS Integration**: Location-based context
- **Indoor Navigation**: Room and furniture recognition
- **Face Recognition**: Identify known people
- **Currency Recognition**: Vietnamese banknote detection
- **Weather Integration**: Include weather in descriptions

### Technical Enhancements
- **Model Optimization**: Faster inference with TensorRT
- **Mobile App**: React Native or Flutter version
- **Cloud Integration**: Improved online processing
- **Multi-language Support**: English and other languages
- **Offline Capabilities**: Fully offline operation mode

### Accessibility
- **Gesture Controls**: Hand gesture recognition
- **Haptic Feedback**: Vibration patterns for navigation
- **Customizable Voice**: Different voice options
- **Audio Cues**: Spatial audio for direction

## 🤝 Đóng góp

Chúng tôi hoan nghênh mọi đóng góp để cải thiện dự án!

### Cách đóng góp

1. **Fork repository** này
2. **Tạo branch** mới (`git checkout -b feature/TinhNangMoi`)
3. **Commit** thay đổi (`git commit -m 'Thêm tính năng mới'`)
4. **Push** lên branch (`git push origin feature/TinhNangMoi`)
5. **Tạo Pull Request**

### Các lĩnh vực cần hỗ trợ
- 🇻🇳 **Cải thiện tiếng Việt**: Từ điển, ngữ pháp, phát âm
- 🤖 **AI/ML**: Tối ưu model, thuật toán mới
- 🎨 **UI/UX**: Thiết kế accessibility, responsive
- 📱 **Mobile**: Phát triển ứng dụng di động
- 📚 **Documentation**: Tài liệu, hướng dẫn, video
- 🧪 **Testing**: Unit tests, integration tests
- 🌐 **Internationalization**: Hỗ trợ đa ngôn ngữ

### Coding Standards
- **Python**: PEP 8, type hints, docstrings
- **TypeScript**: ESLint, Prettier
- **Git**: Conventional commits
- **Tests**: Coverage > 80%


