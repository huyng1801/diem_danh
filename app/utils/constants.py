"""
Application Constants
Định nghĩa các hằng số cho toàn bộ ứng dụng
"""

# ============================================================================
# SYSTEM CONFIGURATIONS
# ============================================================================

# Face Recognition Settings
MIN_FACE_IMAGES = 3                    # Số ảnh tối thiểu để kích hoạt nhận diện
MAX_FACE_IMAGES_PER_STUDENT = 10       # Số ảnh tối đa cho mỗi học sinh
MIN_FACE_CONFIDENCE = 0.80             # Độ tin cậy tối thiểu (80%)
DEFAULT_FACE_CONFIDENCE = 0.6          # Độ tin cậy mặc định
FACE_DISTANCE_THRESHOLD = 0.6          # Ngưỡng khoảng cách khuôn mặt (càng nhỏ càng giống)

# Image Upload Settings
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024       # 5MB
MAX_FILE_SIZE_MB = 5                   # 5MB (alias for templates)
MAX_IMAGE_WIDTH = 1024
MAX_IMAGE_HEIGHT = 1024
THUMBNAIL_WIDTH = 200
THUMBNAIL_HEIGHT = 200

# Classroom Settings
MAX_STUDENTS_PER_CLASS = 45
ALLOWED_GRADES = ['6', '7', '8', '9']
MIN_STUDENTS_PER_CLASS = 20
MAX_STUDENTS_PER_CLASS_OVERFLOW = 50   # Cho phép vượt tạm thời

# Attendance Settings
ATTENDANCE_STATUSES = {
    'present': 'Có mặt',               # Có mặt đúng giờ
    'absent': 'Vắng',                  # Vắng mặt
    'late': 'Muộn',                    # Đi muộn
    'excused': 'Có phép',              # Vắng có phép
}

ATTENDANCE_SESSION_TYPES = {
    'morning': 'Buổi sáng',
    'afternoon': 'Buổi chiều',
}

# Alias for backwards compatibility
SESSION_TYPES = ATTENDANCE_SESSION_TYPES

# Auto-mark absent after (hours)
AUTO_MARK_ABSENT_HOURS = 8

# ============================================================================
# USER & AUTHENTICATION
# ============================================================================

# User Roles
USER_ROLES = {
    'admin': 'Quản trị viên',
    'teacher': 'Giáo viên',
    'staff': 'Nhân viên',
}

# Default Role
DEFAULT_USER_ROLE = 'teacher'

# Password Settings
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 100

# Session Settings
SESSION_TIMEOUT_HOURS = 8
JWT_TOKEN_REFRESH_HOURS = 1

# Login Attempt Restrictions
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCK_MINUTES = 15

# ============================================================================
# DATABASE
# ============================================================================

# Academic Year Format
ACADEMIC_YEAR_FORMAT = r'^\d{4}-\d{4}$'  # YYYY-YYYY format (2024-2025)

# ============================================================================
# FILE PATHS
# ============================================================================

UPLOAD_FOLDER = 'app/uploads'
STUDENT_FACES_FOLDER = 'app/uploads/student_faces'
ATTENDANCE_SNAPSHOTS_FOLDER = 'app/uploads/attendance_snapshots'
TRAINED_MODELS_FOLDER = 'app/uploads/trained_models'
EXCEL_EXPORTS_FOLDER = 'app/uploads/exports'
PDF_EXPORTS_FOLDER = 'app/uploads/exports/pdf'

# Trained Model Filename
TRAINED_MODEL_FILENAME = 'face_recognition_model.pkl'

# ============================================================================
# REPORT & EXPORT SETTINGS
# ============================================================================

# Attendance Rate Classifications
ATTENDANCE_RATE_EXCELLENT = 95         # ≥95% - Chuyên cần
ATTENDANCE_RATE_GOOD = 90              # ≥90% - Đạt

# Excel Export Styles
EXCEL_HEADER_COLOR = '#366092'          # Màu header Excel
EXCEL_STATUS_COLORS = {
    'present': '#4CAF50',               # Xanh lá - Có mặt
    'absent': '#F44336',                # Đỏ - Vắng
    'late': '#FF9800',                  # Cam - Muộn
    'excused': '#2196F3',               # Xanh dương - Có phép
}

# ============================================================================
# API RESPONSE CODES
# ============================================================================

API_SUCCESS_CODE = 200
API_CREATED_CODE = 201
API_BAD_REQUEST_CODE = 400
API_UNAUTHORIZED_CODE = 401
API_FORBIDDEN_CODE = 403
API_NOT_FOUND_CODE = 404
API_CONFLICT_CODE = 409
API_VALIDATION_ERROR_CODE = 422
API_INTERNAL_ERROR_CODE = 500

# ============================================================================
# DATE & TIME FORMATS
# ============================================================================

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%H:%M:%S'
DISPLAY_DATE_FORMAT = '%d/%m/%Y'
DISPLAY_DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_MESSAGES = {
    'INVALID_EMAIL': 'Email không hợp lệ',
    'INVALID_PASSWORD': 'Mật khẩu không đủ mạnh (tối thiểu 8 ký tự, có chữ hoa, chữ thường, số)',
    'INVALID_USERNAME': 'Tên đăng nhập không hợp lệ (3-50 ký tự, chỉ chữ, số, gạch dưới)',
    'INVALID_PHONE': 'Số điện thoại không hợp lệ',
    'INVALID_ACADEMIC_YEAR': 'Niên khóa không hợp lệ (định dạng: YYYY-YYYY)',
    'INVALID_IMAGE_FILE': 'File ảnh không hợp lệ',
    'IMAGE_TOO_LARGE': 'Ảnh quá lớn (tối đa 5MB)',
    'INVALID_ATTENDANCE_STATUS': 'Trạng thái điểm danh không hợp lệ',
    'USER_NOT_FOUND': 'Không tìm thấy người dùng',
    'STUDENT_NOT_FOUND': 'Không tìm thấy học sinh',
    'CLASSROOM_NOT_FOUND': 'Không tìm thấy lớp học',
    'ATTENDANCE_LOG_NOT_FOUND': 'Không tìm thấy phiên điểm danh',
    'DUPLICATE_USERNAME': 'Tên đăng nhập đã tồn tại',
    'DUPLICATE_EMAIL': 'Email đã tồn tại',
    'DUPLICATE_STUDENT_CODE': 'Mã học sinh đã tồn tại',
    'CLASSROOM_FULL': 'Lớp học đã đầy',
    'INSUFFICIENT_FACE_IMAGES': 'Chưa đủ ảnh khuôn mặt để nhận diện',
    'DUPLICATE_ATTENDANCE': 'Học sinh đã điểm danh trong buổi này',
    'UNAUTHORIZED': 'Không có quyền truy cập',
    'FORBIDDEN': 'Truy cập bị cấm',
}
ATTENDANCE_RATE_WARNING = 90           # <90% - Cảnh báo

ATTENDANCE_CLASSIFICATIONS = {
    'excellent': 'Chuyên cần',          # ≥95%
    'good': 'Đạt',                     # ≥90%
    'warning': 'Cảnh báo',             # <90%
}

# Report Date Formats
DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'
TIME_FORMAT = '%H:%M:%S'

# High Absence Threshold
HIGH_ABSENCE_THRESHOLD = 3             # Vắng >3 lần/tuần

# Top Students Limit
TOP_STUDENTS_LIMIT = 10

# ============================================================================
# EXCEL EXPORT COLORS
# ============================================================================

EXCEL_HEADER_COLOR = '366092'          # Dark blue (#366092)
EXCEL_STATUS_COLORS = {
    'present': 'C6EFCE',               # Green
    'absent': 'FFC7CE',                # Red
    'late': 'FFEB9C',                  # Yellow
    'excused': 'BDD7EE',               # Blue
}

# ============================================================================
# FACE RECOGNITION MODEL SETTINGS
# ============================================================================

# Model Type: 'hog' (CPU fast) or 'cnn' (GPU accurate)
FACE_DETECTION_MODEL = 'hog'           # 'hog' hoặc 'cnn'

# Face Encoding Model
FACE_ENCODING_MODEL = 'small'          # Số tầng trong mô hình

# Number of Face Detection Upsamples
FACE_DETECTION_UPSAMPLES = 1

# Video Processing Settings
VIDEO_FRAME_SKIP = 5                   # Xử lý mỗi frame thứ 5 để tối ưu tốc độ
WEBCAM_RESOLUTION = (640, 480)

# ============================================================================
# EMAIL SETTINGS
# ============================================================================

EMAIL_SENDER_NAME = 'Face-ID Attendance System'
EMAIL_FROM = 'noreply@faceid.local'

# Email Templates
EMAIL_TEMPLATES = {
    'welcome': 'Chào mừng đến hệ thống',
    'password_reset': 'Đặt lại mật khẩu',
    'account_locked': 'Tài khoản bị khóa',
}

# ============================================================================
# CACHE SETTINGS
# ============================================================================

CACHE_TRAINED_MODEL = True             # Cache mô hình đã train
CACHE_TIMEOUT_SECONDS = 3600           # 1 hour

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

# ============================================================================
# PAGINATION
# ============================================================================

ITEMS_PER_PAGE = 20
MAX_ITEMS_PER_PAGE = 100

# ============================================================================
# API RESPONSE
# ============================================================================

API_SUCCESS_CODE = 200
API_CREATED_CODE = 201
API_BAD_REQUEST_CODE = 400
API_UNAUTHORIZED_CODE = 401
API_FORBIDDEN_CODE = 403
API_NOT_FOUND_CODE = 404
API_ERROR_CODE = 500

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_MESSAGES = {
    'invalid_email': 'Email không hợp lệ',
    'email_exists': 'Email đã tồn tại',
    'username_exists': 'Tên đăng nhập đã tồn tại',
    'student_code_exists': 'Mã học sinh đã tồn tại',
    'invalid_password': 'Mật khẩu không đúng',
    'account_not_found': 'Tài khoản không tìm thấy',
    'classroom_not_found': 'Lớp học không tìm thấy',
    'student_not_found': 'Học sinh không tìm thấy',
    'invalid_image': 'Định dạng ảnh không hợp lệ',
    'image_too_large': 'Kích thước ảnh quá lớn',
    'invalid_academic_year': 'Niên khóa không hợp lệ',
    'classroom_full': 'Lớp học đã đủ số lượng',
    'duplicate_attendance': 'Học sinh đã điểm danh rồi',
    'permission_denied': 'Bạn không có quyền thực hiện hành động này',
    'invalid_role': 'Vai trò không hợp lệ',
}

# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

SUCCESS_MESSAGES = {
    'login_success': 'Đăng nhập thành công',
    'logout_success': 'Đăng xuất thành công',
    'user_created': 'Tài khoản đã tạo thành công',
    'user_updated': 'Tài khoản đã cập nhật thành công',
    'user_deleted': 'Tài khoản đã vô hiệu hóa thành công',
    'password_changed': 'Mật khẩu đã thay đổi thành công',
    'classroom_created': 'Lớp học đã tạo thành công',
    'student_created': 'Học sinh đã thêm thành công',
    'attendance_recorded': 'Điểm danh đã lưu thành công',
    'model_trained': 'Mô hình đã train thành công',
}
