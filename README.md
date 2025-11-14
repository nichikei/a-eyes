# 👁️ A-Eyes - AI Vision Assistant for the Blind

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![YOLOv5](https://img.shields.io/badge/YOLOv5-Ultralytics-blue)](https://github.com/ultralytics/yolov5)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<div align="center">
  <img src="https://img.shields.io/badge/status-production_ready-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/platform-Windows-blue" alt="Platform">
  <img src="https://img.shields.io/badge/language-Vietnamese-green" alt="Language">
</div>

---

## 🌟 Giới thiệu

**A-Eyes** là hệ thống trợ năng AI tiên tiến, được thiết kế đặc biệt để hỗ trợ người khiếm thị và người mù tại Việt Nam. Sử dụng công nghệ thị giác máy tính hiện đại (Computer Vision), xử lý ngôn ngữ tự nhiên (NLP) và tổng hợp giọng nói (TTS) để cung cấp khả năng "nhìn" và hiểu môi trường xung quanh thông qua âm thanh.

### 🎯 Mục tiêu

Mang lại sự độc lập và an toàn cho người khiếm thị thông qua:
- 🔍 **Nhận diện tức thời**: Phát hiện và mô tả đối tượng trong thời gian thực
- 📍 **Định vị không gian**: Ước tính khoảng cách và vị trí chính xác
- 🧭 **Hướng dẫn di chuyển**: Gợi ý đường đi an toàn, cảnh báo nguy hiểm
- 🗣️ **Phản hồi âm thanh**: Giọng nói tiếng Việt tự nhiên, rõ ràng

### 🏆 Điểm nổi bật

- ✅ **Hoàn toàn miễn phí & mã nguồn mở**
- ✅ **Tối ưu cho người Việt Nam**: Từ vựng, giọng nói, ngữ cảnh địa phương
- ✅ **Xử lý ngoại tuyến**: Không cần kết nối internet liên tục
- ✅ **Hiệu suất cao**: Phản hồi tức thời trên CPU thông thường
- ✅ **Đã kiểm nghiệm thực tế**: Tested với người dùng khiếm thị thực tế

---

## 🎯 Tính năng chính

### 1. 🤖 Nhận diện đối tượng thông minh (Object Detection)

**Công nghệ cốt lõi**: YOLOv5/v8 (Ultralytics) với độ chính xác cao

- **80+ loại đối tượng COCO**: Người, xe cộ, động vật, đồ vật gia dụng, đồ ăn...
- **Từ điển song ngữ đầy đủ**: Anh - Việt cho 60+ đối tượng phổ biến
- **Lọc nhiễu thông minh**: 
  - Ngưỡng confidence động theo từng loại đối tượng
  - Loại bỏ phát hiện sai < 0.3% diện tích khung hình
- **Enhanced Detection System**: 
  - Multi-frame validation: Xác thực qua nhiều khung hình
  - Temporal consistency: Kiểm tra tính nhất quán theo thời gian
  - Confidence trending: Phân tích xu hướng độ tin cậy
  - Spatial stability: Đảm bảo vị trí ổn định

**Performance**: 
- CPU: 5-15 FPS (Intel i5+)
- GPU: 30-60 FPS (NVIDIA GTX 1050+)

---

### 2. 📏 Ước tính khoảng cách & định vị (Distance Estimation)

**Phương pháp**: Tính toán dựa trên tỷ lệ diện tích bbox và đặc điểm đối tượng

#### Ước tính khoảng cách thực tế
```python
# Ví dụ với người (person)
- Diện tích >= 15%: "dưới 2 mét" (nguy hiểm)
- Diện tích 8-15%: "khoảng 3-4 mét" 
- Diện tích 4-8%: "khoảng 5-7 mét"
- Diện tích 2-4%: "khoảng 8-12 mét"
- Diện tích < 2%: "hơn 15 mét"
```

#### Hệ thống định vị đồng hồ (Clock Position)
Mô tả vị trí theo 12 cung (mỗi cung 30°):
- **12 giờ**: Thẳng phía trước
- **3 giờ**: Bên phải
- **6 giờ**: Phía sau
- **9 giờ**: Bên trái

**Ưu điểm**: Dễ hiểu, trực quan cho người khiếm thị

---

### 3. 🧭 Hệ thống điều hướng thông minh (Navigation Guidance)

**Phân tích không gian tự động**:

- ✅ **Phát hiện vùng an toàn**: "Đường đi bên trái thông thoáng"
- ⚠️ **Cảnh báo nguy hiểm**: "Cẩn thận! Xe ô tô rất gần phía trước"
- 🚶 **Gợi ý di chuyển**: "Nên đi về bên phải để tránh chướng ngại vật"

**Thuật toán ưu tiên**:
1. Đối tượng nguy hiểm (xe cộ, chướng ngại vật)
2. Khoảng cách < 3 mét
3. Vị trí phía trước (11-1 giờ)
4. Người và động vật
5. Đồ vật tĩnh

---

### 4. 🗣️ Tổng hợp giọng nói tiếng Việt (Vietnamese TTS)

**Đa engine linh hoạt**:

| Engine | Loại | Ưu điểm | Sử dụng khi |
|--------|------|---------|-------------|
| **Microsoft An (OneCore)** | Offline | Giọng tự nhiên, rõ ràng | Chính (ưu tiên) |
| **SAPI Desktop** | Offline | Ổn định, tích hợp Windows | Fallback 1 |
| **gTTS** | Online | Chất lượng cao | Có internet |
| **pyttsx3** | Offline | Lightweight | Fallback 2 |

**Tối ưu hóa**:
- 🚫 **Chống lặp**: Không lặp lại câu giống nhau trong 4 giây
- ⚡ **Throttling thông minh**: Khoảng cách tối thiểu 1.8s giữa các phát âm
- 🎵 **Điều chỉnh tốc độ**: Rate 190-200 WPM (words per minute)
- 🔊 **Âm lượng tối đa**: Đảm bảo nghe rõ trong môi trường ồn

**Chunking thông minh**:
```python
# Tự động chia câu dài thành đoạn ngắn (max 160 chars)
# Bảo vệ cụm từ đặc biệt: "khung hình", "với kích thước"
```

---

### 5. 💡 Hệ thống mô tả thông minh (Heuristic Captioning)

**Improved Heuristic Caption** - Thuật toán độc quyền:

#### Quy trình xử lý:
```
1. Nhóm đối tượng theo loại
   └─> Counter: {"người": 2, "ghế": 3, "ô tô": 1}

2. Ưu tiên chủ thể chính
   └─> Person > Vehicle > Furniture > Others

3. Tạo template câu tự nhiên
   └─> "Phát hiện 2 người và 1 ô tô"

4. Thêm vị trí & khoảng cách
   └─> "Người thứ nhất ở 2 giờ (lệch phải), khoảng 3-4 mét"

5. Hướng dẫn điều hướng
   └─> "Cẩn thận! Ô tô rất gần phía trước"

6. Gợi ý hành động
   └─> "Nên đi về bên trái"
```

#### Ví dụ output:
```
"Phát hiện 2 người và 1 ô tô. Người thứ nhất ở 2 giờ (lệch phải), 
khoảng 3-4 mét với kích thước vừa. Ô tô ở 12 giờ (thẳng phía trước), 
rất gần - cẩn thận. Nên đi về bên trái để tránh xe."
```

---

### 6. 🛡️ Smart Fallback Detection

**Hệ thống dự phòng khi YOLO không hoạt động**:

- 🎨 **Phân tích màu sắc**: HSV color space analysis
- 🔲 **Phát hiện contours**: Edge detection với Canny
- 🌍 **Nhận diện môi trường**: 
  - `dark_indoor`: Trong nhà tối
  - `bright_indoor`: Trong nhà sáng
  - `outdoor_nature`: Ngoài trời thiên nhiên
  - `outdoor_sky`: Ngoài trời có bầu trời
- 🔍 **Dự đoán đối tượng**: Dựa trên hình dạng và đặc điểm

---

## 🏗️ Kiến trúc hệ thống

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    A-Eyes System Architecture                │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │◄────►│   Backend    │◄────►│  AI Engine   │
│ (Streamlit)  │      │  (FastAPI)   │      │   (PyTorch)  │
└──────────────┘      └──────────────┘      └──────────────┘
       │                      │                      │
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Web Camera  │      │ REST API     │      │ YOLOv5/v8    │
│  (OpenCV)    │      │ /api/describe│      │ Detector     │
└──────────────┘      └──────────────┘      └──────────────┘
                              │                      │
                              │                      ▼
                              │              ┌──────────────┐
                              │              │  Enhanced    │
                              │              │  Detection   │
                              │              └──────────────┘
                              │                      │
                              ▼                      ▼
                      ┌──────────────┐      ┌──────────────┐
                      │ Heuristic    │      │  Captioning  │
                      │ Captioning   │◄─────│  Pipeline    │
                      └──────────────┘      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │ Vietnamese   │
                      │ TTS Engine   │
                      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │ Audio Output │
                      │ (Speakers)   │
                      └──────────────┘
```

---

### 📦 Module Structure

```
a-eyes/
├── 🔧 Core Backend
│   ├── simple_yolo_backend.py      # FastAPI server chính
│   ├── config.yaml                  # Cấu hình hệ thống
│   └── runtime_diag.py              # Diagnostics & device management
│
├── 🤖 AI Detection
│   ├── app/
│   │   ├── detector.py              # YOLO detector wrapper
│   │   ├── processor.py             # Image processing pipeline
│   │   └── video.py                 # Video stream handler
│   ├── enhanced_detection.py        # Multi-frame validation
│   └── smart_fallback.py            # Fallback detection system
│
├── 💬 Captioning & NLP
│   ├── captioning_heuristic.py      # Improved heuristic captions
│   ├── captioning.py                # BLIP/ViTGPT2 models (optional)
│   └── nlp_translate.py             # MarianMT EN→VI translation
│
├── 🔊 Text-to-Speech
│   ├── tts_vn.py                    # Vietnamese TTS manager
│   └── tts_worker.py                # Async TTS queue
│
├── 🖥️ User Interface
│   └── app/
│       ├── boot.py                  # Streamlit app launcher
│       ├── ui_render.py             # UI components
│       └── cam_control.py           # Camera controls
│
└── 🧪 Testing & Scripts
    ├── tests/                       # Unit tests
    ├── scripts/                     # Utility scripts
    └── run_with_optimal_audio.ps1   # Windows launcher
```

---

## 🔧 Tech Stack Chi tiết

### Machine Learning & Computer Vision
| Library | Version | Mục đích |
|---------|---------|----------|
| **PyTorch** | 2.0+ | Deep learning framework |
| **Ultralytics** | 8.0+ | YOLOv5/v8 implementation |
| **OpenCV** | 4.8+ | Image processing & camera |
| **Torchvision** | 0.15+ | Vision transforms |
| **NumPy** | < 2.0 | Numerical computing |
| **Pillow** | 9.0-11.0 | Image manipulation |

### Natural Language Processing
| Library | Version | Mục đích |
|---------|---------|----------|
| **Transformers** | 4.20+ | BLIP, MarianMT models |
| **SentencePiece** | 0.1.99+ | Tokenization |
| **Sacremoses** | 0.0.53+ | Text preprocessing |

### Text-to-Speech & Audio
| Library | Version | Mục đích |
|---------|---------|----------|
| **gTTS** | 2.3+ | Google Text-to-Speech |
| **pyttsx3** | 2.90+ | Offline TTS engine |
| **pywin32** | 306+ | Windows SAPI/OneCore |
| **pygame** | 2.5+ | Audio playback |
| **sounddevice** | 0.4.6+ | Audio I/O |

### Web Framework & API
| Library | Version | Mục đích |
|---------|---------|----------|
| **FastAPI** | Latest | REST API backend |
| **Uvicorn** | Latest | ASGI server |
| **Pydantic** | Latest | Data validation |
| **Streamlit** | 1.28+ | Web UI framework |

### Utilities
| Library | Version | Mục đích |
|---------|---------|----------|
| **PyYAML** | 6.0+ | Config parsing |
| **python-dotenv** | 1.0+ | Environment variables |
| **tqdm** | 4.64+ | Progress bars |
| **pandas** | 1.5+ | Data processing |

---

## 🚀 Cài đặt và sử dụng

### Yêu cầu hệ thống

#### Phần cứng tối thiểu:
- 💻 **CPU**: Intel i5 Gen 8+ / AMD Ryzen 5 3600+
- 🧠 **RAM**: 8GB (khuyên dùng 16GB)
- 📷 **Camera**: Webcam USB 720p+
- 🔊 **Audio**: Loa/Tai nghe (khuyên dùng Bluetooth)

#### Phần cứng khuyên dùng:
- 🎮 **GPU**: NVIDIA GTX 1050+ (CUDA 11+) - tăng tốc 3-5x
- 💾 **Storage**: 10GB trống cho models
- 📹 **Camera**: 1080p với góc rộng

#### Phần mềm:
- 🪟 **OS**: Windows 10/11 (64-bit)
- 🐍 **Python**: 3.11+ (3.11.5 recommended)
- 📦 **Git**: Để clone repository

---

### Cài đặt từng bước

#### 1️⃣ Clone repository
```powershell
git clone https://github.com/nichikei/a-eyes.git
cd a-eyes
```

#### 2️⃣ Tạo Python Virtual Environment
```powershell
# Tạo venv
python -m venv .venv

# Kích hoạt venv (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Nếu gặp lỗi ExecutionPolicy, chạy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3️⃣ Cài đặt Dependencies
```powershell
# Windows (khuyên dùng)
pip install -r requirements-windows.txt

# Hoặc phiên bản cross-platform
pip install -r requirements.txt

# Upgrade pip nếu cần
python -m pip install --upgrade pip
```

#### 4️⃣ Cấu hình Optional (tuỳ chỉnh)

**Chỉnh sửa `config.yaml`**:
```yaml
# Model Configuration
model:
  name: "yolov5s"              # yolov5s (nhanh) | yolov5m (chính xác hơn)
  confidence_threshold: 0.5     # 0.3-0.7 (thấp = nhiều phát hiện)
  device: "cpu"                 # cpu | cuda (nếu có GPU)

# Speech Configuration
speech:
  engine: "gtts"                # gtts (online) | pyttsx3 (offline)
  rate: 190                     # 150-250 (tốc độ đọc)
  volume: 1.0                   # 0.0-1.0
```

#### 5️⃣ Khởi chạy hệ thống

**Phương pháp 1: Sử dụng PowerShell Script (Khuyên dùng)**
```powershell
# Chạy với audio tối ưu
.\run_with_optimal_audio.ps1
```

**Phương pháp 2: Manual**
```powershell
# Kích hoạt venv
.\.venv\Scripts\Activate.ps1

# Chạy backend
python simple_yolo_backend.py

# Backend sẽ chạy tại: http://127.0.0.1:8011
```

**Phương pháp 3: Streamlit App (Web UI)**
```powershell
# Kích hoạt venv
.\.venv\Scripts\Activate.ps1

# Chạy Streamlit
streamlit run app/boot.py

# Mở browser tại: http://localhost:8501
```

---

### 🎮 Sử dụng hệ thống

#### Qua REST API

**Endpoint chính**: `POST /api/describe`

**Request**:
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "autoSpeak": true
}
```

**Response**:
```json
{
  "caption_fast": "Phát hiện 2 người và 1 ô tô. Người thứ nhất ở 2 giờ, khoảng 3-4 mét...",
  "confidence": 0.856,
  "count": 3,
  "objects": ["person", "person", "car"],
  "objects_detail": [
    {
      "en": "person",
      "vi": "người",
      "conf": 0.89,
      "clock": "2 giờ (lệch phải)",
      "range_text": "khoảng 3-4 mét"
    }
  ],
  "processing_time_ms": 245
}
```

#### Qua Streamlit Web UI

1. **Khởi động camera**: Click "Start Camera"
2. **Chế độ tự động**: Bật "Auto Speak" để mô tả liên tục
3. **Chụp thủ công**: Click "Capture Frame"
4. **Xem kết quả**: Tab "Speech History" & "Snapshots"
5. **Điều chỉnh**: Thay đổi confidence threshold trực tiếp trên UI

---

### 🔧 Cấu hình nâng cao

#### Sử dụng GPU (CUDA)

```yaml
# config.yaml
model:
  device: "cuda"
  fp16: true  # Tăng tốc với FP16 precision
```

**Requirements**:
- NVIDIA GPU (GTX 1050+)
- CUDA Toolkit 11.8+
- cuDNN 8.x

```powershell
# Cài đặt PyTorch với CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### Custom Model

```powershell
# Download model tùy chỉnh
# Đặt vào thư mục gốc
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt
```

```yaml
# config.yaml
model:
  name: "yolov5m.pt"  # Model lớn hơn = chính xác hơn
```

#### Tuning Performance

**Để tăng FPS** (giảm độ trễ):
```yaml
processing:
  process_every_n_frames: 3  # Chỉ xử lý mỗi 3 frames
  
model:
  name: "yolov5n"  # Nano model - nhanh nhất
  max_detections: 5  # Giới hạn số đối tượng
```

**Để tăng độ chính xác**:
```yaml
model:
  name: "yolov5l"  # Large model
  confidence_threshold: 0.6  # Ngưỡng cao hơn
  
processing:
  process_every_n_frames: 1  # Xử lý mọi frame
```

---

### 🧪 Testing & Debugging

#### Unit Tests
```powershell
# Test enhanced detection
python test_enhanced_detection.py

# Test Vietnamese TTS
python test_vietnamese_tts.py

# Test long Vietnamese sentences
python test_long_vietnamese.py
```

#### Health Check
```powershell
# Kiểm tra backend status
curl http://127.0.0.1:8011/health

# Kiểm tra TTS voices
curl http://127.0.0.1:8011/tts-voices

# Enhanced detection stats
curl http://127.0.0.1:8011/enhanced-detection-stats
```

#### Debug Mode
```powershell
# Bật debug logging
$env:LOG_LEVEL="DEBUG"
python simple_yolo_backend.py
```

---

### 📊 Monitoring & Performance

#### Metrics Tracking

Backend tự động track:
- ⚡ **Inference time**: Thời gian xử lý YOLO
- 🎯 **Detection count**: Số đối tượng phát hiện
- 🔊 **TTS latency**: Thời gian tổng hợp giọng nói
- 📈 **FPS**: Frames per second

**Xem metrics**:
```powershell
curl http://127.0.0.1:8011/status
```

#### Performance Benchmarks

| Hardware | Model | FPS | Latency |
|----------|-------|-----|---------|
| i5-8400 (CPU) | YOLOv5s | 8-12 FPS | ~120ms |
| i7-10700 (CPU) | YOLOv5s | 12-18 FPS | ~80ms |
| RTX 3060 (GPU) | YOLOv5s | 45-60 FPS | ~20ms |
| RTX 3060 (GPU) | YOLOv5m | 30-40 FPS | ~30ms |

---

## 🤝 Đóng góp (Contributing)

Chúng tôi hoan nghênh mọi đóng góp! Dự án này được xây dựng với mục đích phi lợi nhuận, phục vụ cộng đồng người khiếm thị Việt Nam.

### Cách đóng góp

1. **Fork repository**
2. **Tạo branch mới**: `git checkout -b feature/AmazingFeature`
3. **Commit changes**: `git commit -m 'Add some AmazingFeature'`
4. **Push to branch**: `git push origin feature/AmazingFeature`
5. **Open Pull Request**

### Hướng phát triển

- [ ] **Mobile App**: Android/iOS native app
- [ ] **Nhận diện chữ viết**: OCR tiếng Việt (Tesseract/EasyOCR)
- [ ] **Nhận diện khuôn mặt**: Face recognition cho người thân
- [ ] **Navigation GPS**: Tích hợp bản đồ và chỉ đường
- [ ] **Cloud API**: Deploy lên Azure/AWS cho mobile
- [ ] **Multi-language**: Hỗ trợ English, Thai, Indonesia
- [ ] **Voice commands**: Điều khiển bằng giọng nói

### Bug Reports & Feature Requests

- 🐛 **Bug report**: [GitHub Issues](https://github.com/nichikei/a-eyes/issues)
- 💡 **Feature request**: [GitHub Discussions](https://github.com/nichikei/a-eyes/discussions)

---

## 📝 License

Dự án này được phân phối dưới **MIT License**. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

```
MIT License

Copyright (c) 2024 A-Eyes Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Acknowledgments

### Contributors
- **Core Team**: [nichikei](https://github.com/nichikei)
- **Community**: Người dùng khiếm thị đã tham gia test và feedback

### Open Source Libraries
- [Ultralytics YOLOv5/v8](https://github.com/ultralytics/yolov5) - Object detection
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [PyTorch](https://pytorch.org/) - Deep learning
- [gTTS](https://github.com/pndurette/gTTS) - Text-to-speech
- [Streamlit](https://streamlit.io/) - Web UI

### Inspiration
- Dự án được lấy cảm hứng từ nhu cầu thực tế của cộng đồng người khiếm thị Việt Nam
- Mục tiêu: Công nghệ AI phải phục vụ con người, đặc biệt là những người cần hỗ trợ nhất

---

## 📞 Liên hệ & Hỗ trợ

- 📧 **Email**: support@a-eyes.vn (nếu có)
- 💬 **Discord**: [A-Eyes Community](https://discord.gg/a-eyes) (nếu có)
- 🐛 **Issues**: [GitHub Issues](https://github.com/nichikei/a-eyes/issues)
- 📖 **Docs**: [Wiki](https://github.com/nichikei/a-eyes/wiki)

---

## ⭐ Support the Project

Nếu dự án này hữu ích với bạn, hãy:
- ⭐ **Star** repository trên GitHub
- 🔄 **Share** với cộng đồng
- 🐛 **Report bugs** để cải thiện
- 💡 **Suggest features** mới
- 🤝 **Contribute** code hoặc documentation

---

<div align="center">
  
### 💙 Made with love for the visually impaired community in Vietnam

**A-Eyes** - *Empowering the blind through AI*

[⬆ Back to top](#-a-eyes---ai-vision-assistant-for-the-blind)

</div>

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


