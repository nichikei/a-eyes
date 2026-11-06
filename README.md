# 👁️ A-Eyes — trợ lý thị giác tiếng Việt cho người khiếm thị

Camera chụp khung hình → YOLO nhận diện vật thể (80 lớp COCO) → mô tả tiếng Việt kèm
**hướng kim đồng hồ** và **khoảng cách ước lượng** → đọc bằng giọng Việt (Microsoft An).

```
web/ (React + TypeScript, Vite)   ──POST /api/describe (JPEG base64)──▶   simple_yolo_backend.py (FastAPI)
                                                                            ├─ app/detector.py         Ultralytics YOLO (PyTorch hoặc OpenVINO)
                                                                            ├─ enhanced_detection.py   ngưỡng tin cậy theo ánh sáng + xác thực đa khung hình
                                                                            ├─ smart_fallback.py       dự phòng không cần YOLO: HSV + Canny
                                                                            ├─ captioning_heuristic.py câu tiếng Việt: đối tượng, hướng, khoảng cách, cảnh báo
                                                                            └─ tts_vn.py / tts_worker  giọng Việt (OneCore / SAPI / pyttsx3), chạy nền
```

## Tính năng

- **Nhận diện**: YOLOv5su (Ultralytics, pretrained COCO), lọc theo ngưỡng tin cậy riêng từng lớp
  và loại box nhỏ hơn 0,3% khung hình.
- **Tiếng Việt cho cả 80/80 lớp COCO** — không còn đọc tên tiếng Anh bằng giọng Việt.
- **Hướng kim đồng hồ**: chia bề ngang khung hình thành 5 cung 10 · 11 · 12 · 1 · 2 giờ.
- **Khoảng cách**: ước lượng theo tỷ lệ diện tích box và loại vật (người, xe, đồ nội thất…),
  cảnh báo "NGUY HIỂM" khi xe ở rất gần.
- **Giọng nói không chặn request**: TTS chạy trên một worker nền, các câu không chồng nhau,
  câu trùng lặp bị bỏ qua.
- **Dự phòng**: khi không tải được YOLO, phân tích màu HSV + biên Canny (~30 ms/khung hình).

## Hiệu năng (đo thật)

`python scripts/benchmark.py --model <model>` — chạy pipeline `/api/describe` trong tiến trình
(giải mã JPEG → YOLO → lọc → câu tiếng Việt) trên khung hình 1280×720 JPEG q80, đúng kích thước
web client gửi; 40 lần/ảnh trên 2 ảnh mẫu của Ultralytics.

Máy: Intel Core i7-1355U (laptop, chỉ CPU), Python 3.11, torch 2.8 CPU.

| Model | Độ trễ p50 end-to-end | FPS | Kết quả nhận diện |
|---|---|---|---|
| `yolov5su.pt` (PyTorch) | ~440 ms | ~2,3 | bus + 4 người; 2 người + cà vạt |
| `yolov5su_openvino_model` | **~60 ms** | **~17** | giống hệt |

Xuất model OpenVINO một lần (backend tự dùng nếu thư mục tồn tại):

```bash
pip install openvino
yolo export model=yolov5su.pt format=openvino imgsz=640
```

Bước lọc nâng cao trước đây tính thống kê ảnh trên toàn khung 1280×720 (~150 ms); nay tính trên
ảnh thu nhỏ 320 px, chỉ còn vài ms.

## Chạy

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python simple_yolo_backend.py          # http://127.0.0.1:8011, tự tải yolov5su.pt lần đầu

cd web && npm install && npm run dev   # http://localhost:5173 (proxy /api → :8011)
```

Biến môi trường: `YOLO_MODEL`, `YOLO_CONF`, `YOLO_IMGSZ`, `CAPTION_DEVICE` (`auto|cpu|cuda`),
`MIN_AREA_RATIO`, `DEFAULT_MIN_CONF`, `BACKEND_PORT`.

## API

| Method | Path | Mô tả |
|---|---|---|
| POST | `/api/describe` | `{image, autoSpeak}` → câu mô tả, danh sách vật, hướng, khoảng cách, `timings_ms` |
| GET | `/health` | trạng thái, thiết bị, detector đã tải chưa |
| GET | `/tts-voices` | các giọng SAPI/OneCore có trên máy |

## Kiểm thử

```bash
python -m pytest tests -q     # 124 test, ~5 s, không cần model hay GPU (detector giả)
```

Bao gồm: phủ nhãn tiếng Việt 80 lớp, hướng kim đồng hồ, lọc box, API end-to-end, và hồi quy
"response không chờ TTS".

## Giới hạn

- Khoảng cách là ước lượng theo kích thước box, không phải đo độ sâu.
- Hướng dựa trên vị trí ngang trong khung hình, giả định camera hướng thẳng phía trước.
- Giọng đọc phía server cần Windows (OneCore/SAPI); web client có thể tự đọc bằng Web Speech API.

## License

MIT
