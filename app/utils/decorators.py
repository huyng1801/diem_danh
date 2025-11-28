"""
Decorators for Role-Based Access Control
Các decorator để kiểm soát truy cập dựa trên vai trò người dùng
"""

from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models.user import User
from app.utils.constants import (
    USER_ROLES, API_UNAUTHORIZED_CODE, API_FORBIDDEN_CODE, 
    ERROR_MESSAGES, JWT_TOKEN_REFRESH_HOURS
)
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# JWT AUTHENTICATION DECORATOR
# ============================================================================

def login_required(f):
    """
    Decorator để kiểm tra xem người dùng đã đăng nhập hay chưa (JWT Token hoặc Session)
    Yêu cầu header: Authorization: Bearer <token> hoặc session
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session, redirect, url_for
        
        # Check session first (for web interface)
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user and user.is_active:
                request.current_user = user
                request.user_id = user.id
                request.user_role = user.role
                return f(*args, **kwargs)
            else:
                # Session exists but user invalid - clear session and redirect
                logger.warning(f'Invalid session detected, clearing...')
                session.clear()
                if request.accept_mimetypes.accept_html:
                    return redirect(url_for('auth.login_page'))
                return jsonify({
                    'success': False,
                    'message': 'Phiên đăng nhập không hợp lệ',
                    'status_code': API_UNAUTHORIZED_CODE
                }), API_UNAUTHORIZED_CODE
        
        # Check JWT token (for API)
        token = None
        
        # Lấy token từ header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                # For web interface, redirect to login
                if request.accept_mimetypes.accept_html:
                    return redirect(url_for('auth.login_page'))
                return jsonify({
                    'success': False,
                    'message': 'Token không hợp lệ',
                    'status_code': API_UNAUTHORIZED_CODE
                }), API_UNAUTHORIZED_CODE
        
        if not token:
            # For web interface, redirect to login
            if request.accept_mimetypes.accept_html:
                return redirect(url_for('auth.login_page'))
            return jsonify({
                'success': False,
                'message': 'Token bị thiếu',
                'status_code': API_UNAUTHORIZED_CODE
            }), API_UNAUTHORIZED_CODE
        
        try:
            # Decode JWT token
            secret = current_app.config.get('SECRET_KEY', 'your-secret-key')
            decoded_token = jwt.decode(token, secret, algorithms=['HS256'])
            
            # Lấy user từ database
            user = User.query.get(decoded_token['user_id'])
            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Tài khoản không tồn tại hoặc đã bị vô hiệu hóa',
                    'status_code': API_UNAUTHORIZED_CODE
                }), API_UNAUTHORIZED_CODE
            
            # Lưu user vào request context
            request.current_user = user
            request.user_id = user.id
            request.user_role = user.role
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Token đã hết hạn',
                'status_code': API_UNAUTHORIZED_CODE
            }), API_UNAUTHORIZED_CODE
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Token không hợp lệ',
                'status_code': API_UNAUTHORIZED_CODE
            }), API_UNAUTHORIZED_CODE
        except Exception as e:
            logger.error(f'Error decoding token: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'Lỗi xác thực',
                'status_code': API_UNAUTHORIZED_CODE
            }), API_UNAUTHORIZED_CODE
    
    return decorated_function

# ============================================================================
# ROLE-BASED ACCESS CONTROL DECORATORS
# ============================================================================

def role_required(*roles):
    """
    Decorator để kiểm tra xem người dùng có role được phép hay không
    
    Usage:
        @app.route('/admin')
        @role_required('admin')
        def admin_page():
            pass
        
        @app.route('/manage')
        @role_required('admin', 'teacher')
        def manage_page():
            pass
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if request.user_role not in roles:
                logger.warning(
                    f'Access denied for user {request.user_id} '
                    f'role {request.user_role} accessing {f.__name__}'
                )
                return jsonify({
                    'success': False,
                    'message': ERROR_MESSAGES['permission_denied'],
                    'status_code': API_FORBIDDEN_CODE
                }), API_FORBIDDEN_CODE
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorator để chỉ cho phép admin truy cập
    """
    @wraps(f)
    @role_required('admin')
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """
    Decorator để chỉ cho phép teacher và admin truy cập
    """
    @wraps(f)
    @role_required('teacher', 'admin')
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# CUSTOM ACCESS CONTROL DECORATORS
# ============================================================================

def can_edit_classroom(f):
    """
    Decorator để kiểm tra xem người dùng có quyền chỉnh sửa lớp học hay không
    Admin: có thể chỉnh sửa tất cả lớp
    Teacher: chỉ có thể chỉnh sửa lớp mà họ là head_teacher
    """
    @wraps(f)
    @login_required
    def decorated_function(classroom_id, *args, **kwargs):
        from app.models.class_room import ClassRoom
        
        classroom = ClassRoom.query.get(classroom_id)
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Lớp học không tìm thấy',
                'status_code': 404
            }), 404
        
        # Admin có quyền truy cập tất cả
        if request.user_role == 'admin':
            return f(classroom_id, *args, **kwargs)
        
        # Teacher chỉ có thể chỉnh sửa lớp của mình
        if request.user_role == 'teacher':
            if classroom.head_teacher_id != request.user_id:
                return jsonify({
                    'success': False,
                    'message': ERROR_MESSAGES['permission_denied'],
                    'status_code': API_FORBIDDEN_CODE
                }), API_FORBIDDEN_CODE
            return f(classroom_id, *args, **kwargs)
        
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES['permission_denied'],
            'status_code': API_FORBIDDEN_CODE
        }), API_FORBIDDEN_CODE
    
    return decorated_function

def can_edit_attendance(f):
    """
    Decorator để kiểm tra xem người dùng có quyền chỉnh sửa điểm danh hay không
    Admin: có thể chỉnh sửa tất cả
    Teacher: chỉ có thể chỉnh sửa điểm danh của lớp mình phụ trách
    """
    @wraps(f)
    @login_required
    def decorated_function(attendance_id, *args, **kwargs):
        from app.models.attendance import Attendance
        
        attendance = Attendance.query.get(attendance_id)
        if not attendance:
            return jsonify({
                'success': False,
                'message': 'Bản điểm danh không tìm thấy',
                'status_code': 404
            }), 404
        
        # Admin có quyền truy cập tất cả
        if request.user_role == 'admin':
            return f(attendance_id, *args, **kwargs)
        
        # Teacher chỉ có thể chỉnh sửa điểm danh của lớp mình
        if request.user_role == 'teacher':
            classroom = attendance.classroom
            if classroom.head_teacher_id != request.user_id:
                return jsonify({
                    'success': False,
                    'message': ERROR_MESSAGES['permission_denied'],
                    'status_code': API_FORBIDDEN_CODE
                }), API_FORBIDDEN_CODE
            return f(attendance_id, *args, **kwargs)
        
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES['permission_denied'],
            'status_code': API_FORBIDDEN_CODE
        }), API_FORBIDDEN_CODE
    
    return decorated_function

def can_view_classroom_data(f):
    """
    Decorator để kiểm tra xem người dùng có quyền xem dữ liệu lớp học hay không
    Admin: có thể xem tất cả
    Teacher: chỉ có thể xem lớp mình phụ trách
    """
    @wraps(f)
    @login_required
    def decorated_function(classroom_id, *args, **kwargs):
        from app.models.class_room import ClassRoom
        
        classroom = ClassRoom.query.get(classroom_id)
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Lớp học không tìm thấy',
                'status_code': 404
            }), 404
        
        # Admin có quyền truy cập tất cả
        if request.user_role == 'admin':
            return f(classroom_id, *args, **kwargs)
        
        # Teacher chỉ có thể xem lớp của mình
        if request.user_role == 'teacher':
            if classroom.head_teacher_id != request.user_id:
                return jsonify({
                    'success': False,
                    'message': ERROR_MESSAGES['permission_denied'],
                    'status_code': API_FORBIDDEN_CODE
                }), API_FORBIDDEN_CODE
            return f(classroom_id, *args, **kwargs)
        
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES['permission_denied'],
            'status_code': API_FORBIDDEN_CODE
        }), API_FORBIDDEN_CODE
    
    return decorated_function

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_current_user():
    """
    Lấy user hiện tại từ request context
    Chỉ sử dụng sau khi @login_required decorator
    """
    return getattr(request, 'current_user', None)

def get_current_user_id():
    """
    Lấy ID của user hiện tại
    """
    return getattr(request, 'user_id', None)

def get_current_user_role():
    """
    Lấy role của user hiện tại
    """
    return getattr(request, 'user_role', None)

def is_admin():
    """
    Kiểm tra xem user hiện tại có phải admin hay không
    """
    return get_current_user_role() == 'admin'

def is_teacher():
    """
    Kiểm tra xem user hiện tại có phải teacher hay không
    """
    return get_current_user_role() == 'teacher'

def is_staff():
    """
    Kiểm tra xem user hiện tại có phải staff hay không
    """
    return get_current_user_role() == 'staff'
