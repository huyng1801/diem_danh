"""
Utils Package
Các module hỗ trợ cho ứng dụng
"""

# Import constants
from app.utils.constants import (
    # Face Recognition Settings
    MIN_FACE_IMAGES,
    MAX_FACE_IMAGES_PER_STUDENT,
    MIN_FACE_CONFIDENCE,
    DEFAULT_FACE_CONFIDENCE,
    FACE_DISTANCE_THRESHOLD,
    
    # Image Upload Settings
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE,
    
    # Classroom Settings
    MAX_STUDENTS_PER_CLASS,
    ALLOWED_GRADES,
    
    # Attendance Settings
    ATTENDANCE_STATUSES,
    ATTENDANCE_SESSION_TYPES,
    AUTO_MARK_ABSENT_HOURS,
    
    # User & Authentication
    USER_ROLES,
    MIN_PASSWORD_LENGTH,
    SESSION_TIMEOUT_HOURS,
    JWT_TOKEN_REFRESH_HOURS,
    
    # File Paths
    STUDENT_FACES_FOLDER,
    ATTENDANCE_SNAPSHOTS_FOLDER,
    TRAINED_MODELS_FOLDER,
    
    # Error & Success Messages
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
)

# Import decorators
from app.utils.decorators import (
    login_required,
    role_required,
    admin_required,
    teacher_required,
    can_edit_classroom,
    can_edit_attendance,
    can_view_classroom_data,
    get_current_user,
    get_current_user_id,
    get_current_user_role,
    is_admin,
    is_teacher,
    is_staff,
)

# Import validators
from app.utils.validators import (
    is_valid_email,
    is_valid_username,
    is_valid_password,
    is_valid_image_format,
    is_valid_image_size,
    validate_image_file,
    is_valid_name,
    is_valid_student_code,
    is_valid_classroom_name,
    is_valid_phone,
    is_valid_address,
    is_valid_date,
    is_valid_date_range,
    is_valid_academic_year,
    is_valid_grade,
    is_valid_attendance_status,
    is_valid_confidence_score,
    validate_user_data,
    validate_student_data,
    validate_classroom_data,
)

# Import helpers
from app.utils.helpers import (
    ensure_upload_directories,
    get_upload_path,
    get_student_faces_path,
    delete_file,
    delete_directory,
    get_current_datetime,
    get_current_date,
    get_current_time,
    format_datetime,
    format_date,
    format_time,
    parse_datetime,
    get_date_range,
    get_date_after_days,
    get_week_start,
    get_week_end,
    get_month_start,
    get_month_end,
    generate_jwt_token,
    decode_jwt_token,
    generate_unique_filename,
    sanitize_filename,
    truncate_text,
    generate_random_string,
    round_to_decimal,
    calculate_percentage,
    format_percentage,
    create_success_response,
    create_error_response,
    create_paginated_response,
    log_action,
    classify_attendance_rate,
    get_attendance_color,
)

# Import email helper
from app.utils.email_helper import (
    send_email,
    send_welcome_email,
    send_password_reset_email,
    send_account_locked_email,
    send_attendance_report_email,
    send_bulk_email,
    is_valid_email_format,
    validate_email_list,
)

__all__ = [
    # Constants
    'MIN_FACE_IMAGES',
    'MAX_FACE_IMAGES_PER_STUDENT',
    'MIN_FACE_CONFIDENCE',
    'DEFAULT_FACE_CONFIDENCE',
    'ALLOWED_IMAGE_EXTENSIONS',
    'MAX_IMAGE_SIZE',
    'MAX_STUDENTS_PER_CLASS',
    'ALLOWED_GRADES',
    'ATTENDANCE_STATUSES',
    'ATTENDANCE_SESSION_TYPES',
    'AUTO_MARK_ABSENT_HOURS',
    'USER_ROLES',
    'MIN_PASSWORD_LENGTH',
    'SESSION_TIMEOUT_HOURS',
    'JWT_TOKEN_REFRESH_HOURS',
    'STUDENT_FACES_FOLDER',
    'ATTENDANCE_SNAPSHOTS_FOLDER',
    'TRAINED_MODELS_FOLDER',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    
    # Decorators
    'login_required',
    'role_required',
    'admin_required',
    'teacher_required',
    'can_edit_classroom',
    'can_edit_attendance',
    'can_view_classroom_data',
    'get_current_user',
    'get_current_user_id',
    'get_current_user_role',
    'is_admin',
    'is_teacher',
    'is_staff',
    
    # Validators
    'is_valid_email',
    'is_valid_username',
    'is_valid_password',
    'is_valid_image_format',
    'is_valid_image_size',
    'validate_image_file',
    'is_valid_name',
    'is_valid_student_code',
    'is_valid_classroom_name',
    'is_valid_phone',
    'is_valid_address',
    'is_valid_date',
    'is_valid_date_range',
    'is_valid_academic_year',
    'is_valid_grade',
    'is_valid_attendance_status',
    'is_valid_confidence_score',
    'validate_user_data',
    'validate_student_data',
    'validate_classroom_data',
    
    # Helpers
    'ensure_upload_directories',
    'get_upload_path',
    'get_student_faces_path',
    'delete_file',
    'delete_directory',
    'get_current_datetime',
    'get_current_date',
    'get_current_time',
    'format_datetime',
    'format_date',
    'format_time',
    'parse_datetime',
    'get_date_range',
    'get_date_after_days',
    'get_week_start',
    'get_week_end',
    'get_month_start',
    'get_month_end',
    'generate_jwt_token',
    'decode_jwt_token',
    'generate_unique_filename',
    'sanitize_filename',
    'truncate_text',
    'generate_random_string',
    'round_to_decimal',
    'calculate_percentage',
    'format_percentage',
    'create_success_response',
    'create_error_response',
    'create_paginated_response',
    'log_action',
    'classify_attendance_rate',
    'get_attendance_color',
    
    # Email Helper
    'send_email',
    'send_welcome_email',
    'send_password_reset_email',
    'send_account_locked_email',
    'send_attendance_report_email',
    'send_bulk_email',
    'is_valid_email_format',
    'validate_email_list',
]
