/**
 * Face Recognition Module
 * Handles camera operations, face detection, and attendance recording
 */

class FaceRecognitionCamera {
    constructor(config = {}) {
        this.config = {
            videoElement: config.videoElement || '#camera-video',
            canvasElement: config.canvasElement || '#camera-canvas',
            captureButton: config.captureButton || '#capture-btn',
            switchCameraButton: config.switchCameraButton || '#switch-camera-btn',
            stopButton: config.stopButton || '#stop-camera-btn',
            previewElement: config.previewElement || '#captured-preview',
            statusElement: config.statusElement || '#camera-status',
            attendanceEndpoint: config.attendanceEndpoint || '/api/attendance/mark',
            detectEndpoint: config.detectEndpoint || '/api/face/detect',
            width: config.width || 640,
            height: config.height || 480,
            ...config
        };

        this.stream = null;
        this.devices = [];
        this.currentDeviceIndex = 0;
        this.isRecording = false;
        this.detectionInterval = null;
        
        this.init();
    }

    async init() {
        try {
            this.setupElements();
            this.setupEventListeners();
            await this.getDevices();
        } catch (error) {
            console.error('Failed to initialize camera:', error);
            this.showError('Không thể khởi tạo camera. Vui lòng kiểm tra quyền truy cập camera.');
        }
    }

    setupElements() {
        this.video = document.querySelector(this.config.videoElement);
        this.canvas = document.querySelector(this.config.canvasElement);
        this.captureBtn = document.querySelector(this.config.captureButton);
        this.switchBtn = document.querySelector(this.config.switchCameraButton);
        this.stopBtn = document.querySelector(this.config.stopButton);
        this.preview = document.querySelector(this.config.previewElement);
        this.status = document.querySelector(this.config.statusElement);

        if (this.canvas) {
            this.ctx = this.canvas.getContext('2d');
            this.canvas.width = this.config.width;
            this.canvas.height = this.config.height;
        }
    }

    setupEventListeners() {
        if (this.captureBtn) {
            this.captureBtn.addEventListener('click', () => this.capturePhoto());
        }

        if (this.switchBtn) {
            this.switchBtn.addEventListener('click', () => this.switchCamera());
        }

        if (this.stopBtn) {
            this.stopBtn.addEventListener('click', () => this.stopCamera());
        }

        // Start camera automatically when video element is visible
        if (this.video) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !this.stream) {
                        this.startCamera();
                    }
                });
            });
            observer.observe(this.video);
        }
    }

    async getDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.devices = devices.filter(device => device.kind === 'videoinput');
            
            if (this.devices.length === 0) {
                throw new Error('Không tìm thấy camera nào');
            }

            this.updateCameraControls();
        } catch (error) {
            console.error('Error getting devices:', error);
            throw error;
        }
    }

    updateCameraControls() {
        if (this.switchBtn) {
            this.switchBtn.style.display = this.devices.length > 1 ? 'inline-block' : 'none';
        }
    }

    async startCamera(deviceId = null) {
        try {
            this.showStatus('Đang khởi động camera...', 'info');
            
            if (this.stream) {
                this.stopCamera();
            }

            const constraints = {
                video: {
                    width: { ideal: this.config.width },
                    height: { ideal: this.config.height },
                    facingMode: deviceId ? undefined : 'user'
                }
            };

            if (deviceId) {
                constraints.video.deviceId = { exact: deviceId };
            }

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            if (this.video) {
                this.video.srcObject = this.stream;
                this.video.play();
                
                this.video.addEventListener('loadedmetadata', () => {
                    this.showStatus('Camera đã sẵn sàng', 'success');
                    this.startDetection();
                });
            }

            this.isRecording = true;
            this.updateButtons();

        } catch (error) {
            console.error('Error starting camera:', error);
            this.showError('Không thể khởi động camera. Vui lòng kiểm tra quyền truy cập.');
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.video) {
            this.video.srcObject = null;
        }

        this.stopDetection();
        this.isRecording = false;
        this.updateButtons();
        this.showStatus('Camera đã dừng', 'warning');
    }

    async switchCamera() {
        if (this.devices.length <= 1) return;

        this.currentDeviceIndex = (this.currentDeviceIndex + 1) % this.devices.length;
        const device = this.devices[this.currentDeviceIndex];
        
        await this.startCamera(device.deviceId);
    }

    capturePhoto() {
        if (!this.video || !this.canvas || !this.isRecording) {
            this.showError('Camera chưa sẵn sàng');
            return null;
        }

        try {
            // Draw video frame to canvas
            this.ctx.drawImage(this.video, 0, 0, this.config.width, this.config.height);
            
            // Get image data
            const imageData = this.canvas.toDataURL('image/jpeg', 0.8);
            
            // Show preview
            if (this.preview) {
                this.preview.src = imageData;
                this.preview.style.display = 'block';
            }

            this.showStatus('Đã chụp ảnh thành công!', 'success');
            
            return imageData;
        } catch (error) {
            console.error('Error capturing photo:', error);
            this.showError('Lỗi khi chụp ảnh');
            return null;
        }
    }

    startDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }

        // Auto-detect faces every 3 seconds
        this.detectionInterval = setInterval(() => {
            this.detectFaces();
        }, 3000);
    }

    stopDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
    }

    async detectFaces() {
        if (!this.isRecording) return;

        try {
            const imageData = this.capturePhoto();
            if (!imageData) return;

            const response = await FaceID.APIClient.post(this.config.detectEndpoint, {
                image: imageData,
                timestamp: new Date().toISOString()
            });

            if (response.success && response.faces && response.faces.length > 0) {
                this.handleDetectedFaces(response.faces);
            }
        } catch (error) {
            console.error('Face detection error:', error);
        }
    }

    handleDetectedFaces(faces) {
        const faceCount = faces.length;
        let message = `Phát hiện ${faceCount} khuôn mặt`;
        
        const recognizedFaces = faces.filter(face => face.student_id);
        if (recognizedFaces.length > 0) {
            message += ` (${recognizedFaces.length} đã nhận diện)`;
            this.showStatus(message, 'success');
            
            // Auto-mark attendance for recognized faces
            recognizedFaces.forEach(face => {
                this.markAttendance(face.student_id, face.confidence);
            });
        } else {
            this.showStatus(message, 'info');
        }
    }

    async markAttendance(studentId, confidence) {
        try {
            const response = await FaceID.APIClient.post(this.config.attendanceEndpoint, {
                student_id: studentId,
                confidence: confidence,
                timestamp: new Date().toISOString(),
                method: 'face_recognition'
            });

            if (response.success) {
                FaceID.NotificationSystem.success(
                    `Điểm danh thành công cho học sinh: ${response.student_name || studentId}`
                );
            }
        } catch (error) {
            console.error('Attendance marking error:', error);
            FaceID.NotificationSystem.error('Lỗi khi điểm danh tự động');
        }
    }

    updateButtons() {
        if (this.captureBtn) {
            this.captureBtn.disabled = !this.isRecording;
        }
        
        if (this.stopBtn) {
            this.stopBtn.disabled = !this.isRecording;
        }
        
        if (this.switchBtn) {
            this.switchBtn.disabled = !this.isRecording;
        }
    }

    showStatus(message, type = 'info') {
        if (this.status) {
            const iconClass = this.getStatusIcon(type);
            const colorClass = this.getStatusColor(type);
            
            this.status.innerHTML = `
                <i class="${iconClass} me-2"></i>
                <span class="text-${colorClass}">${message}</span>
            `;
        }
        
        console.log(`Camera Status [${type}]:`, message);
    }

    showError(message) {
        this.showStatus(message, 'error');
        FaceID.NotificationSystem.error(message);
    }

    getStatusIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    getStatusColor(type) {
        const colors = {
            success: 'success',
            error: 'danger',
            warning: 'warning',
            info: 'info'
        };
        return colors[type] || colors.info;
    }

    destroy() {
        this.stopCamera();
        this.stopDetection();
    }
}

/**
 * Face Recognition Utilities
 */
const FaceRecognitionUtils = {
    // Initialize camera for attendance page
    initAttendanceCamera() {
        return new FaceRecognitionCamera({
            videoElement: '#attendance-video',
            canvasElement: '#attendance-canvas',
            captureButton: '#capture-attendance',
            switchCameraButton: '#switch-camera',
            stopButton: '#stop-camera',
            previewElement: '#captured-preview',
            statusElement: '#camera-status',
            attendanceEndpoint: '/api/attendance/mark'
        });
    },

    // Initialize camera for student registration
    initRegistrationCamera() {
        return new FaceRecognitionCamera({
            videoElement: '#registration-video',
            canvasElement: '#registration-canvas',
            captureButton: '#capture-face',
            switchCameraButton: '#switch-camera',
            stopButton: '#stop-camera',
            previewElement: '#face-preview',
            statusElement: '#camera-status',
            detectEndpoint: '/api/face/register',
            width: 400,
            height: 300
        });
    },

    // Validate image file for face upload
    validateImageFile(file) {
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        const maxSize = 5 * 1024 * 1024; // 5MB

        if (!validTypes.includes(file.type)) {
            FaceID.NotificationSystem.error('Chỉ chấp nhận file ảnh định dạng JPG, JPEG, PNG');
            return false;
        }

        if (file.size > maxSize) {
            FaceID.NotificationSystem.error('Kích thước file không được vượt quá 5MB');
            return false;
        }

        return true;
    },

    // Preview uploaded image
    previewImage(input, previewElement) {
        const file = input.files[0];
        if (!file || !this.validateImageFile(file)) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.querySelector(previewElement);
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(file);
    },

    // Upload multiple face images
    async uploadFaceImages(studentId, files) {
        if (!files || files.length === 0) {
            FaceID.NotificationSystem.error('Vui lòng chọn ít nhất một ảnh');
            return false;
        }

        const formData = new FormData();
        formData.append('student_id', studentId);

        let validFiles = 0;
        for (let file of files) {
            if (this.validateImageFile(file)) {
                formData.append('images', file);
                validFiles++;
            }
        }

        if (validFiles === 0) {
            FaceID.NotificationSystem.error('Không có file ảnh hợp lệ nào');
            return false;
        }

        try {
            FaceID.LoadingManager.show(null, 'Đang tải ảnh lên...');

            const response = await fetch('/api/student/upload-faces', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                FaceID.NotificationSystem.success(
                    `Đã tải lên thành công ${result.uploaded_count}/${validFiles} ảnh`
                );
                return true;
            } else {
                throw new Error(result.message || 'Lỗi khi tải ảnh lên');
            }
        } catch (error) {
            console.error('Upload error:', error);
            FaceID.NotificationSystem.error('Lỗi khi tải ảnh lên: ' + error.message);
            return false;
        } finally {
            FaceID.LoadingManager.hide();
        }
    }
};

// Auto-initialize based on page
FaceID.DOMUtils.ready(() => {
    // Initialize camera on attendance page
    if (document.querySelector('#attendance-video')) {
        window.attendanceCamera = FaceRecognitionUtils.initAttendanceCamera();
    }

    // Initialize camera on student registration page
    if (document.querySelector('#registration-video')) {
        window.registrationCamera = FaceRecognitionUtils.initRegistrationCamera();
    }

    // Setup file upload handlers
    const faceUploadInput = document.querySelector('#face-upload-input');
    if (faceUploadInput) {
        faceUploadInput.addEventListener('change', function() {
            FaceRecognitionUtils.previewImage(this, '#face-upload-preview');
        });
    }

    // Setup multiple face upload
    const multipleFaceUpload = document.querySelector('#multiple-face-upload');
    if (multipleFaceUpload) {
        multipleFaceUpload.addEventListener('change', function() {
            const files = Array.from(this.files);
            const previewContainer = document.querySelector('#multiple-preview-container');
            
            if (previewContainer) {
                previewContainer.innerHTML = '';
                files.forEach((file, index) => {
                    if (FaceRecognitionUtils.validateImageFile(file)) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const previewDiv = FaceID.DOMUtils.createElement('div', 'col-md-3 mb-3');
                            previewDiv.innerHTML = `
                                <div class="card">
                                    <img src="${e.target.result}" class="card-img-top" style="height: 150px; object-fit: cover;">
                                    <div class="card-body text-center p-2">
                                        <small class="text-muted">Ảnh ${index + 1}</small>
                                    </div>
                                </div>
                            `;
                            previewContainer.appendChild(previewDiv);
                        };
                        reader.readAsDataURL(file);
                    }
                });
            }
        });
    }
});

// Export for global use
window.FaceID = window.FaceID || {};
window.FaceID.Camera = FaceRecognitionCamera;
window.FaceID.FaceUtils = FaceRecognitionUtils;
