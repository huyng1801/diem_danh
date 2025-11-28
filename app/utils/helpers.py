"""
Helper Functions
Các hàm hỗ trợ thường dùng trong ứng dụng
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import jwt
from flask import current_app
from app.utils.constants import (
    DATE_FORMAT, DATETIME_FORMAT, TIME_FORMAT,
    STUDENT_FACES_FOLDER, ATTENDANCE_SNAPSHOTS_FOLDER,
    TRAINED_MODELS_FOLDER, EXCEL_EXPORTS_FOLDER, PDF_EXPORTS_FOLDER,
    UPLOAD_FOLDER, JWT_TOKEN_REFRESH_HOURS
)

logger = logging.getLogger(__name__)

# ============================================================================
# FILE MANAGEMENT HELPERS
# ============================================================================

def ensure_upload_directories():
    """
    Tạo các thư mục upload nếu chúng không tồn tại
    """
    directories = [
        UPLOAD_FOLDER,
        STUDENT_FACES_FOLDER,
        ATTENDANCE_SNAPSHOTS_FOLDER,
        TRAINED_MODELS_FOLDER,
        EXCEL_EXPORTS_FOLDER,
        PDF_EXPORTS_FOLDER,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f'Directory ensured: {directory}')

def get_upload_path(folder):
    """
    Lấy đường dẫn thư mục upload
    """
    path = os.path.join(UPLOAD_FOLDER, folder)
    os.makedirs(path, exist_ok=True)
    return path

def get_student_faces_path(student_code):
    """
    Lấy đường dẫn thư mục ảnh khuôn mặt của học sinh
    """
    path = os.path.join(STUDENT_FACES_FOLDER, student_code)
    os.makedirs(path, exist_ok=True)
    return path

def delete_file(filepath):
    """
    Xóa file khỏi ổ cứng
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f'File deleted: {filepath}')
            return True
    except Exception as e:
        logger.error(f'Error deleting file {filepath}: {str(e)}')
    return False

def delete_directory(directory):
    """
    Xóa thư mục và tất cả nội dung
    """
    try:
        if os.path.exists(directory):
            import shutil
            shutil.rmtree(directory)
            logger.info(f'Directory deleted: {directory}')
            return True
    except Exception as e:
        logger.error(f'Error deleting directory {directory}: {str(e)}')
    return False

def get_file_size(filepath):
    """
    Lấy kích thước file (bytes)
    """
    try:
        return os.path.getsize(filepath)
    except Exception as e:
        logger.error(f'Error getting file size: {str(e)}')
        return 0

def get_file_size_mb(filepath):
    """
    Lấy kích thước file (MB)
    """
    size_bytes = get_file_size(filepath)
    return size_bytes / (1024 * 1024)

# ============================================================================
# DATE & TIME HELPERS
# ============================================================================

def get_current_datetime():
    """
    Lấy ngày giờ hiện tại
    """
    return datetime.now()

def get_current_date():
    """
    Lấy ngày hiện tại
    """
    return datetime.now().date()

def get_current_time():
    """
    Lấy giờ hiện tại
    """
    return datetime.now().time()

def format_datetime(dt, format_str=DATETIME_FORMAT):
    """
    Định dạng datetime thành chuỗi
    """
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    return str(dt)

def format_date(date_obj, format_str=DATE_FORMAT):
    """
    Định dạng date thành chuỗi
    """
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime(format_str)
    return str(date_obj)

def format_time(time_obj, format_str=TIME_FORMAT):
    """
    Định dạng time thành chuỗi
    """
    if hasattr(time_obj, 'strftime'):
        return time_obj.strftime(format_str)
    return str(time_obj)

def parse_datetime(datetime_string, format_str=DATETIME_FORMAT):
    """
    Chuyển đổi chuỗi thành datetime object
    """
    try:
        return datetime.strptime(datetime_string, format_str)
    except ValueError:
        return None

def get_date_range(start_date, end_date):
    """
    Lấy danh sách tất cả các ngày trong khoảng thời gian
    """
    if isinstance(start_date, str):
        start_date = parse_datetime(start_date, DATE_FORMAT).date()
    if isinstance(end_date, str):
        end_date = parse_datetime(end_date, DATE_FORMAT).date()
    
    current = start_date
    dates = []
    
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    
    return dates

def get_date_after_days(date_obj, days):
    """
    Lấy ngày sau N ngày
    """
    if isinstance(date_obj, str):
        date_obj = parse_datetime(date_obj, DATE_FORMAT).date()
    
    return date_obj + timedelta(days=days)

def get_week_start(date_obj):
    """
    Lấy ngày đầu tiên của tuần (Thứ Hai)
    """
    if isinstance(date_obj, str):
        date_obj = parse_datetime(date_obj, DATE_FORMAT).date()
    
    return date_obj - timedelta(days=date_obj.weekday())

def get_week_end(date_obj):
    """
    Lấy ngày cuối cùng của tuần (Chủ Nhật)
    """
    week_start = get_week_start(date_obj)
    return week_start + timedelta(days=6)

def get_month_start(date_obj):
    """
    Lấy ngày đầu tiên của tháng
    """
    if isinstance(date_obj, str):
        date_obj = parse_datetime(date_obj, DATE_FORMAT).date()
    
    return date_obj.replace(day=1)

def get_month_end(date_obj):
    """
    Lấy ngày cuối cùng của tháng
    """
    if isinstance(date_obj, str):
        date_obj = parse_datetime(date_obj, DATE_FORMAT).date()
    
    next_month = date_obj.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)

def get_days_ago(days):
    """
    Lấy ngày cách đây N ngày
    """
    return datetime.now().date() - timedelta(days=days)

def get_hours_ago(hours):
    """
    Lấy thời gian cách đây N giờ
    """
    return datetime.now() - timedelta(hours=hours)

# ============================================================================
# JWT TOKEN HELPERS
# ============================================================================

def generate_jwt_token(user_id, user_role, expires_in_hours=24):
    """
    Tạo JWT token cho user
    """
    try:
        secret = current_app.config.get('SECRET_KEY', 'your-secret-key')
        payload = {
            'user_id': user_id,
            'user_role': user_role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
        }
        token = jwt.encode(payload, secret, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f'Error generating JWT token: {str(e)}')
        return None

def decode_jwt_token(token):
    """
    Giải mã JWT token
    """
    try:
        secret = current_app.config.get('SECRET_KEY', 'your-secret-key')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning('JWT token expired')
        return None
    except jwt.InvalidTokenError:
        logger.warning('Invalid JWT token')
        return None
    except Exception as e:
        logger.error(f'Error decoding JWT token: {str(e)}')
        return None

# ============================================================================
# STRING HELPERS
# ============================================================================

def generate_unique_filename(original_filename):
    """
    Tạo tên file duy nhất
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(original_filename)
    return f'{name}_{timestamp}{ext}'

def sanitize_filename(filename):
    """
    Làm sạch tên file (loại bỏ ký tự không hợp lệ)
    """
    import re
    # Giữ lại chỉ chữ, số, dấu gạch ngang, dấu gạch dưới, dấu chấm
    filename = re.sub(r'[^\w\-.]', '', filename)
    return filename

def truncate_text(text, max_length=100, suffix='...'):
    """
    Cắt ngắn text nếu vượt quá độ dài tối đa
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def generate_random_string(length=10):
    """
    Tạo chuỗi ngẫu nhiên
    """
    import string
    import random
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# ============================================================================
# NUMBER HELPERS
# ============================================================================

def round_to_decimal(value, decimal_places=2):
    """
    Làm tròn số đến số thập phân
    """
    return round(float(value), decimal_places)

def calculate_percentage(numerator, denominator, decimal_places=2):
    """
    Tính phần trăm
    """
    if denominator == 0:
        return 0
    return round_to_decimal((numerator / denominator) * 100, decimal_places)

def format_percentage(value, decimal_places=1):
    """
    Định dạng phần trăm
    """
    return f'{round_to_decimal(value, decimal_places)}%'

# ============================================================================
# RESPONSE HELPERS
# ============================================================================

def create_success_response(data=None, message='Success', status_code=200):
    """
    Tạo response thành công
    """
    response = {
        'success': True,
        'message': message,
        'status_code': status_code,
    }
    if data is not None:
        response['data'] = data
    return response

def create_error_response(message='Error', error_code='ERROR', status_code=400, details=None):
    """
    Tạo response lỗi
    """
    response = {
        'success': False,
        'message': message,
        'error_code': error_code,
        'status_code': status_code,
    }
    if details is not None:
        response['details'] = details
    return response

def create_paginated_response(items, total, page, per_page, message='Success'):
    """
    Tạo response có phân trang
    """
    total_pages = (total + per_page - 1) // per_page
    return {
        'success': True,
        'message': message,
        'data': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
        }
    }

# ============================================================================
# LOGGING HELPERS
# ============================================================================

def log_action(user_id, action, entity_type, entity_id, details=None):
    """
    Ghi log hành động của user
    """
    try:
        logger.info(f'Action: User {user_id} {action} {entity_type} {entity_id}')
        if details:
            logger.info(f'Details: {details}')
    except Exception as e:
        logger.error(f'Error logging activity: {str(e)}')

# ============================================================================
# CLASSIFICATION HELPERS
# ============================================================================

def classify_attendance_rate(rate):
    """
    Phân loại tỷ lệ điểm danh
    """
    from app.utils.constants import (
        ATTENDANCE_RATE_EXCELLENT,
        ATTENDANCE_RATE_GOOD,
        ATTENDANCE_CLASSIFICATIONS
    )
    
    if rate >= ATTENDANCE_RATE_EXCELLENT:
        return ATTENDANCE_CLASSIFICATIONS['excellent']
    elif rate >= ATTENDANCE_RATE_GOOD:
        return ATTENDANCE_CLASSIFICATIONS['good']
    else:
        return ATTENDANCE_CLASSIFICATIONS['warning']

def get_attendance_color(status):
    """
    Lấy màu cho trạng thái điểm danh
    """
    from app.utils.constants import EXCEL_STATUS_COLORS
    
    colors = {
        'present': EXCEL_STATUS_COLORS['present'],
        'absent': EXCEL_STATUS_COLORS['absent'],
        'late': EXCEL_STATUS_COLORS['late'],
        'excused': EXCEL_STATUS_COLORS['excused'],
    }
    return colors.get(status, 'FFFFFF')

# ============================================================================
# JINJA2 TEMPLATE HELPERS
# ============================================================================

def get_status_badge_class(status):
    """Get Bootstrap badge class for attendance status"""
    status_classes = {
        'present': 'bg-success',
        'late': 'bg-warning',
        'excused': 'bg-info',
        'absent': 'bg-danger'
    }
    return status_classes.get(status, 'bg-secondary')


def get_status_display(status):
    """Get display name for attendance status"""
    status_names = {
        'present': 'Có mặt',
        'late': 'Muộn',
        'excused': 'Có phép',
        'absent': 'Vắng'
    }
    return status_names.get(status, status)


def get_confidence_badge_class(confidence):
    """Get Bootstrap badge class for confidence level"""
    if confidence is None or confidence == 0:
        return 'bg-secondary'
    if confidence >= 0.9:
        return 'bg-success'
    if confidence >= 0.7:
        return 'bg-warning text-dark'
    return 'bg-danger'


def get_confidence_progress_class(confidence):
    """Get Bootstrap progress bar class for confidence level"""
    if confidence is None or confidence == 0:
        return 'bg-secondary'
    if confidence >= 0.9:
        return 'bg-success'
    if confidence >= 0.7:
        return 'bg-warning'
    return 'bg-danger'

