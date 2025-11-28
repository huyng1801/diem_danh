"""
Validators for Input Data Validation
Các hàm xác thực dữ liệu đầu vào
"""

import re
import logging
from datetime import datetime
from app.utils.constants import (
    ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE, MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH, ERROR_MESSAGES, ALLOWED_GRADES,
    ACADEMIC_YEAR_FORMAT, ATTENDANCE_STATUSES
)

logger = logging.getLogger(__name__)

# ============================================================================
# EMAIL VALIDATORS
# ============================================================================

def is_valid_email(email):
    """
    Kiểm tra xem email có hợp lệ hay không
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_username(username):
    """
    Kiểm tra xem tên đăng nhập có hợp lệ hay không
    Yêu cầu: 3-50 ký tự, chỉ chứa chữ, số, dấu gạch dưới
    """
    if not username or not isinstance(username, str):
        return False
    
    if len(username) < 3 or len(username) > 50:
        return False
    
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

# ============================================================================
# PASSWORD VALIDATORS
# ============================================================================

def is_valid_password(password):
    """
    Kiểm tra xem mật khẩu có hợp lệ hay không
    Yêu cầu: 8-100 ký tự, ít nhất 1 chữ hoa, 1 chữ thường, 1 số
    """
    if not password or not isinstance(password, str):
        return False
    
    if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        return False
    
    # Ít nhất 1 chữ hoa
    if not re.search(r'[A-Z]', password):
        return False
    
    # Ít nhất 1 chữ thường
    if not re.search(r'[a-z]', password):
        return False
    
    # Ít nhất 1 số
    if not re.search(r'\d', password):
        return False
    
    return True

def get_password_strength(password):
    """
    Lấy độ mạnh của mật khẩu (1-4)
    1: Yếu, 2: Trung bình, 3: Tốt, 4: Rất tốt
    """
    if not is_valid_password(password):
        return 0
    
    strength = 1
    
    # Nếu độ dài ≥12, tăng độ mạnh
    if len(password) >= 12:
        strength += 1
    
    # Nếu có ký tự đặc biệt, tăng độ mạnh
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        strength += 1
    
    # Nếu độ dài ≥16, tăng độ mạnh lên tối đa
    if len(password) >= 16:
        strength = 4
    
    return strength

# ============================================================================
# IMAGE VALIDATORS
# ============================================================================

def is_valid_image_format(filename):
    """
    Kiểm tra xem định dạng ảnh có hợp lệ hay không
    """
    if not filename or '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS

def is_valid_image_size(file_size):
    """
    Kiểm tra xem kích thước ảnh có hợp lệ hay không
    """
    return 0 < file_size <= MAX_IMAGE_SIZE

def is_valid_image_file(file):
    """
    Kiểm tra xem file ảnh có hợp lệ hay không (wrapper function)
    Trả về: True nếu hợp lệ, False nếu không
    """
    is_valid, _ = validate_image_file(file)
    return is_valid

def validate_image_file(file):
    """
    Xác thực file ảnh (format và kích thước)
    Trả về: (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, 'File không được để trống'
    
    if not is_valid_image_format(file.filename):
        extensions = ', '.join(ALLOWED_IMAGE_EXTENSIONS)
        return False, f'Định dạng ảnh không hợp lệ. Chỉ chấp nhận: {extensions}'
    
    # Lấy kích thước file
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)     # Reset to beginning
    
    if not is_valid_image_size(file_size):
        max_size_mb = MAX_IMAGE_SIZE / (1024 * 1024)
        return False, f'Kích thước ảnh quá lớn. Tối đa {max_size_mb:.1f}MB'
    
    return True, None

# ============================================================================
# NAME VALIDATORS
# ============================================================================

def is_valid_name(name):
    """
    Kiểm tra xem tên có hợp lệ hay không
    Yêu cầu: 2-100 ký tự, không chứa ký tự đặc biệt
    """
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    if len(name) < 2 or len(name) > 100:
        return False
    
    # Cho phép chữ, số, dấu cách, dấu gạch ngang, dấu ngoặc
    pattern = r'^[a-zA-Z0-9\s\-()àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+$'
    return re.match(pattern, name, re.IGNORECASE) is not None

def is_valid_student_code(student_code):
    """
    Kiểm tra xem mã học sinh có hợp lệ hay không
    Yêu cầu: 5-20 ký tự, chỉ chứa chữ, số, dấu gạch ngang
    """
    if not student_code or not isinstance(student_code, str):
        return False
    
    student_code = student_code.strip()
    
    if len(student_code) < 5 or len(student_code) > 20:
        return False
    
    pattern = r'^[a-zA-Z0-9\-]+$'
    return re.match(pattern, student_code) is not None

def is_valid_classroom_name(classroom_name):
    """
    Kiểm tra xem tên lớp có hợp lệ hay không
    VD: 6A1, 7B2, 8C3, 9A1
    """
    if not classroom_name or not isinstance(classroom_name, str):
        return False
    
    classroom_name = classroom_name.strip()
    
    if len(classroom_name) < 2 or len(classroom_name) > 10:
        return False
    
    # Định dạng: số + chữ + số (VD: 6A1)
    pattern = r'^[6-9][A-Za-z]\d{1,2}$'
    return re.match(pattern, classroom_name) is not None

# ============================================================================
# PHONE & ADDRESS VALIDATORS
# ============================================================================

def is_valid_phone(phone):
    """
    Kiểm tra xem số điện thoại có hợp lệ hay không
    Cho phép: +84, 0 ở đầu, các ký tự như dấu cách, dấu gạch ngang, ngoặc
    """
    if not phone or not isinstance(phone, str):
        return False
    
    phone = phone.strip()
    
    # Loại bỏ các ký tự không phải số (giữ lại +)
    phone_digits = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Kiểm tra độ dài: ít nhất 7 chữ số, tối đa 15 chữ số (theo E.164)
    if len(phone_digits) < 7 or len(phone_digits) > 15:
        return False
    
    # Nếu bắt đầu bằng + hoặc 0, hoặc là số hợp lệ
    if phone_digits.startswith('+'):
        return len(phone_digits) >= 10
    
    return True

def is_valid_address(address):
    """
    Kiểm tra xem địa chỉ có hợp lệ hay không
    """
    if not address or not isinstance(address, str):
        return False
    
    address = address.strip()
    return 5 <= len(address) <= 200

# ============================================================================
# DATE & TIME VALIDATORS
# ============================================================================

def is_valid_date(date_string, date_format='%d/%m/%Y'):
    """
    Kiểm tra xem ngày tháng có hợp lệ hay không
    """
    if not date_string:
        return False
    
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False

def is_valid_date_range(start_date, end_date, date_format='%d/%m/%Y'):
    """
    Kiểm tra xem khoảng thời gian có hợp lệ hay không
    (ngày kết thúc phải sau ngày bắt đầu)
    """
    try:
        start = datetime.strptime(start_date, date_format)
        end = datetime.strptime(end_date, date_format)
        return end > start
    except ValueError:
        return False

def parse_date(date_string, date_format='%d/%m/%Y'):
    """
    Chuyển đổi chuỗi ngày tháng thành datetime object
    """
    try:
        return datetime.strptime(date_string, date_format)
    except ValueError:
        return None

# ============================================================================
# ACADEMIC YEAR VALIDATORS
# ============================================================================

def is_valid_academic_year(academic_year):
    """
    Kiểm tra xem niên khóa có hợp lệ hay không (YYYY-YYYY)
    """
    if not academic_year or not isinstance(academic_year, str):
        return False
    
    pattern = ACADEMIC_YEAR_FORMAT
    if not re.match(pattern, academic_year):
        return False
    
    try:
        start_year, end_year = academic_year.split('-')
        start_year = int(start_year)
        end_year = int(end_year)
        
        # end_year phải = start_year + 1
        return end_year == start_year + 1 and start_year >= 2000
    except (ValueError, IndexError):
        return False

def parse_academic_year(academic_year):
    """
    Tách niên khóa thành start_year và end_year
    """
    if not is_valid_academic_year(academic_year):
        return None, None
    
    start_year, end_year = academic_year.split('-')
    return int(start_year), int(end_year)

# ============================================================================
# CLASSROOM VALIDATORS
# ============================================================================

def is_valid_grade(grade):
    """
    Kiểm tra xem khối lớp có hợp lệ hay không
    """
    return grade in ALLOWED_GRADES

# ============================================================================
# ATTENDANCE VALIDATORS
# ============================================================================

def is_valid_attendance_status(status):
    """
    Kiểm tra xem trạng thái điểm danh có hợp lệ hay không
    """
    return status in ATTENDANCE_STATUSES

# ============================================================================
# CONFIDENCE VALIDATORS
# ============================================================================

def is_valid_confidence_score(confidence):
    """
    Kiểm tra xem điểm tin cậy có hợp lệ hay không (0.0 - 1.0 hoặc 0 - 100)
    """
    try:
        conf = float(confidence)
        return 0 <= conf <= 1 or 0 <= conf <= 100
    except (ValueError, TypeError):
        return False

def normalize_confidence_score(confidence):
    """
    Chuẩn hóa điểm tin cậy về khoảng 0-1
    """
    try:
        conf = float(confidence)
        if conf > 1:
            return conf / 100
        return conf
    except (ValueError, TypeError):
        return None

# ============================================================================
# BATCH VALIDATORS
# ============================================================================

def validate_user_data(data):
    """
    Xác thực dữ liệu người dùng
    """
    errors = {}
    
    # Username
    if 'username' in data:
        if not is_valid_username(data['username']):
            errors['username'] = 'Tên đăng nhập phải 3-50 ký tự, chỉ chứa chữ, số, dấu gạch dưới'
    
    # Email
    if 'email' in data:
        if not is_valid_email(data['email']):
            errors['email'] = 'Email không hợp lệ'
    
    # Password
    if 'password' in data:
        if not is_valid_password(data['password']):
            errors['password'] = f'Mật khẩu phải {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} ký tự, ít nhất 1 chữ hoa, 1 chữ thường, 1 số'
    
    # Full name
    if 'full_name' in data:
        if not is_valid_name(data['full_name']):
            errors['full_name'] = 'Tên không hợp lệ (2-100 ký tự)'
    
    # Phone
    if 'phone' in data and data['phone']:
        if not is_valid_phone(data['phone']):
            errors['phone'] = 'Số điện thoại không hợp lệ'
    
    return errors

def validate_student_data(data):
    """
    Xác thực dữ liệu học sinh
    """
    errors = {}
    
    # Student Code
    if 'student_code' in data:
        if not is_valid_student_code(data['student_code']):
            errors['student_code'] = 'Mã học sinh phải 5-20 ký tự'
    
    # Full Name
    if 'full_name' in data:
        if not is_valid_name(data['full_name']):
            errors['full_name'] = 'Tên học sinh không hợp lệ'
    
    # Date of Birth
    if 'date_of_birth' in data:
        if not is_valid_date(data['date_of_birth']):
            errors['date_of_birth'] = 'Ngày sinh không hợp lệ'
    
    # Address
    if 'address' in data and data['address']:
        if not is_valid_address(data['address']):
            errors['address'] = 'Địa chỉ không hợp lệ'
    
    return errors

def validate_classroom_data(data):
    """
    Xác thực dữ liệu lớp học
    """
    errors = {}
    
    # Classroom Name
    if 'classroom_name' in data:
        if not is_valid_classroom_name(data['classroom_name']):
            errors['classroom_name'] = 'Tên lớp không hợp lệ (VD: 6A1, 7B2)'
    
    # Grade
    if 'grade' in data:
        if not is_valid_grade(data['grade']):
            errors['grade'] = f'Khối lớp phải là một trong: {ALLOWED_GRADES}'
    
    return errors

# ============================================================================
# ACADEMIC YEAR VALIDATORS
# ============================================================================

def is_valid_academic_year(year):
    """
    Kiểm tra định dạng niên khóa (YYYY-YYYY)
    """
    if not year or not isinstance(year, str):
        return False
    
    if not re.match(ACADEMIC_YEAR_FORMAT, year):
        return False
    
    start_year, end_year = map(int, year.split('-'))
    if end_year != start_year + 1:
        return False
    
    return True

# ============================================================================
# ATTENDANCE VALIDATORS
# ============================================================================

def is_valid_attendance_status(status):
    """
    Kiểm tra trạng thái điểm danh có hợp lệ không
    """
    return status in ATTENDANCE_STATUSES

def is_valid_session_type(session_type):
    """
    Kiểm tra loại buổi học có hợp lệ không
    """
    valid_sessions = ['morning', 'afternoon']
    return session_type in valid_sessions

def is_valid_confidence_score(confidence):
    """
    Kiểm tra độ tin cậy nhận diện có hợp lệ không (0.0 - 1.0)
    """
    try:
        score = float(confidence)
        return 0.0 <= score <= 1.0
    except (ValueError, TypeError):
        return False

# ============================================================================
# PHONE VALIDATORS
# ============================================================================

def is_valid_phone(phone):
    """
    Kiểm tra số điện thoại Việt Nam có hợp lệ không
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove spaces and dashes
    phone = re.sub(r'[\s\-]', '', phone)
    
    # Vietnamese phone patterns
    patterns = [
        r'^(\+84|84|0)(3|5|7|8|9)[0-9]{8}$',  # Mobile
        r'^(\+84|84|0)(2[0-9])[0-9]{8}$',     # Landline
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    
    return False

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_attendance_data(data):
    """
    Xác thực dữ liệu điểm danh
    """
    errors = {}
    
    # Status
    if 'status' in data:
        if not is_valid_attendance_status(data['status']):
            errors['status'] = ERROR_MESSAGES['INVALID_ATTENDANCE_STATUS']
    
    # Confidence score
    if 'face_confidence' in data and data['face_confidence'] is not None:
        if not is_valid_confidence_score(data['face_confidence']):
            errors['face_confidence'] = 'Độ tin cậy phải từ 0.0 đến 1.0'
    
    # Session type
    if 'session_type' in data:
        if not is_valid_session_type(data['session_type']):
            errors['session_type'] = 'Loại buổi học không hợp lệ'
    
    return errors
