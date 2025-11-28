# Face Recognition System

Hệ thống nhận diện khuôn mặt sử dụng thư viện `face_recognition` và `OpenCV`.

## Tính năng

### 1. Face Trainer (`face_trainer.py`)
- **Train model từ ảnh học sinh**: Xử lý ảnh có cả thân và mặt người (không chỉ ảnh cắt mặt)
- **Tự động resize ảnh**: Xử lý ảnh lớn để tăng tốc độ
- **Batch training**: Train nhiều người cùng lúc
- **Lưu model**: Lưu encodings vào file pickle để sử dụng sau
- **Logging chi tiết**: Theo dõi quá trình training

### 2. Face Detector (`face_detector.py`)
- **Nhận diện khuôn mặt trong ảnh**: Từ file ảnh
- **Nhận diện real-time**: Từ webcam/camera
- **Vẽ bounding box**: Hiển thị tên và độ tin cậy
- **Lưu kết quả**: Lưu ảnh đã xử lý
- **Điều chỉnh confidence threshold**: Kiểm soát độ chính xác

## Cấu trúc thư mục

```
app/uploads/
├── student_faces/          # Ảnh gốc học sinh (để train)
│   ├── Nguyen Van A/      # Mỗi người 1 folder
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   └── ...
│   ├── Tran Thi B/
│   │   └── ...
│   └── ...
└── trained_models/         # Model đã train
    └── face_encodings.pkl
```

## Cách sử dụng

### 1. Training Model

#### Cách 1: Chạy trực tiếp file
```bash
cd ml_models
python face_trainer.py
```

#### Cách 2: Import trong code
```python
from ml_models import FaceTrainer

# Khởi tạo trainer
trainer = FaceTrainer()

# Train tất cả học sinh
results = trainer.train_all(
    model="hog",        # Hoặc "cnn" (chính xác hơn nhưng cần GPU)
    min_images=2,       # Số ảnh tối thiểu mỗi người
    save_model=True     # Lưu model sau khi train
)

# Xem kết quả
print(f"Trained: {results['trained_count']}/{results['total_persons']}")
print(f"Total encodings: {results['total_encodings']}")

# Train một người cụ thể
success, message, encodings = trainer.train_person("Nguyen Van A")
```

### 2. Face Detection & Recognition

#### Cách 1: Chạy trực tiếp file (Video real-time)
```bash
cd ml_models
python face_detector.py
```
- Nhấn 'q' để thoát
- Nhấn 's' để lưu snapshot

#### Cách 2: Nhận diện từ ảnh
```python
from ml_models import FaceDetector

# Khởi tạo detector
detector = FaceDetector(confidence_threshold=0.6)

# Load model đã train
detector.load_model()

# Nhận diện từ file ảnh
result = detector.process_image_file(
    image_path="path/to/image.jpg",
    save_result=True,      # Lưu ảnh kết quả
    output_dir="output/"   # Thư mục lưu kết quả
)

# Xem kết quả
for face in result['faces']:
    print(f"Name: {face['name']}")
    print(f"Confidence: {face['confidence']:.2f}")
    print(f"Location: {face['location']}")
```

#### Cách 3: Nhận diện real-time từ webcam
```python
from ml_models import FaceDetector

detector = FaceDetector(confidence_threshold=0.6)
detector.load_model()

# Start video recognition
detector.start_video_recognition(
    camera_index=0,    # 0 = camera mặc định
    model="hog",       # "hog" nhanh hơn, "cnn" chính xác hơn
    frame_skip=2       # Xử lý mỗi 2 frame để tăng tốc
)
```

#### Cách 4: Tích hợp vào Flask app
```python
import cv2
import numpy as np
from ml_models import FaceDetector

detector = FaceDetector(confidence_threshold=0.6)
detector.load_model()

# Nhận diện từ frame camera
def recognize_from_frame(frame_data):
    # Convert frame data to numpy array
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Recognize faces
    faces = detector.recognize_faces_in_image(rgb_frame)
    
    return faces
```

## Tham số quan trọng

### Face Trainer
- **model**: 
  - `"hog"`: Nhanh, phù hợp CPU, độ chính xác tốt
  - `"cnn"`: Chính xác hơn, cần GPU để chạy nhanh
- **min_images**: Số ảnh tối thiểu mỗi người (khuyến nghị: >= 3)
- **num_jitters**: Số lần xử lý mỗi ảnh (cao = chính xác hơn nhưng chậm hơn)

### Face Detector
- **confidence_threshold**: Ngưỡng tin cậy (0.0 - 1.0)
  - 0.4 - 0.5: Rất chặt, ít false positive
  - 0.6: Cân bằng (khuyến nghị)
  - 0.7 - 0.8: Lỏng hơn, nhiều kết quả hơn
- **frame_skip**: Số frame bỏ qua trong video (cao = nhanh hơn nhưng ít mượt hơn)

## Xử lý ảnh

### Ảnh đầu vào
- **Format**: JPG, JPEG, PNG, BMP, GIF
- **Nội dung**: Ảnh có cả phần thân trên và mặt người (không cần cắt)
- **Chất lượng**: 
  - Mặt rõ ràng, không bị mờ
  - Ánh sáng đủ
  - Góc chụp không quá nghiêng
- **Số lượng**: Ít nhất 3-5 ảnh mỗi người với góc độ khác nhau

### Xử lý tự động
- Resize ảnh lớn (> 1024px) để tăng tốc
- Detect face trong ảnh có nhiều người
- Extract face encoding 128 chiều
- Lưu encoding để so sánh sau

## Performance Tips

1. **Training**:
   - Sử dụng `model="hog"` cho CPU
   - Sử dụng `model="cnn"` nếu có GPU
   - Giảm `num_jitters` nếu quá chậm

2. **Detection**:
   - Tăng `frame_skip` cho video real-time
   - Sử dụng `model="hog"` cho real-time
   - Giảm resolution camera nếu cần

3. **Accuracy**:
   - Train với nhiều ảnh đa dạng (góc độ, ánh sáng khác nhau)
   - Điều chỉnh `confidence_threshold` phù hợp
   - Sử dụng `model="cnn"` cho độ chính xác cao

## Troubleshooting

### Lỗi "No face detected"
- Kiểm tra chất lượng ảnh (độ phân giải, ánh sáng)
- Thử đổi model từ "hog" sang "cnn"
- Kiểm tra góc chụp (mặt phải nhìn thấy rõ)

### Train chậm
- Giảm `num_jitters` trong `extract_face_encodings`
- Sử dụng `model="hog"` thay vì "cnn"
- Giảm số lượng ảnh hoặc resize ảnh nhỏ hơn

### Nhận diện sai
- Tăng số ảnh training cho mỗi người
- Giảm `confidence_threshold`
- Kiểm tra chất lượng ảnh training
- Re-train model với ảnh tốt hơn

### Video lag
- Tăng `frame_skip`
- Giảm resolution camera
- Sử dụng `model="hog"`

## Examples

Xem file `train_and_test.py` để có ví dụ đầy đủ.
