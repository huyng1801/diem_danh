"""
Authentication Routes
Các endpoint để đăng nhập, đăng xuất, đăng ký tài khoản
"""

from flask import Blueprint, request, jsonify, session
import jwt
from datetime import datetime, timedelta
from functools import wraps
from app import db
from app.models.user import User
from app.services.user_service import UserService
from app.utils.decorators import login_required
from app.utils.validators import (
    is_valid_email, is_valid_password, is_valid_username
)
from app.utils.constants import (
    USER_ROLES, ERROR_MESSAGES, API_SUCCESS_CODE, 
    API_UNAUTHORIZED_CODE, API_BAD_REQUEST_CODE, API_CREATED_CODE
)
from flask import current_app
import logging

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

def generate_jwt_token(user):
    """Generate JWT token for user"""
    try:
        secret = current_app.config.get('SECRET_KEY', 'your-secret-key')
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }, secret, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f'Error generating JWT token: {str(e)}')
        return None

# ============================================================================
# ROUTES
# ============================================================================

@auth_bp.route('/debug-session', methods=['GET'])
def debug_session():
    """Debug session info"""
    from flask import render_template, current_app
    
    session_info = {
        'session_data': dict(session),
        'has_user_id': 'user_id' in session,
        'secret_key_set': bool(current_app.config.get('SECRET_KEY')),
        'session_cookie_secure': current_app.config.get('SESSION_COOKIE_SECURE'),
        'permanent_session_lifetime': str(current_app.config.get('PERMANENT_SESSION_LIFETIME')),
    }
    
    return jsonify(session_info)

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """
    Display login page
    GET /auth/login
    """
    from flask import render_template
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """
    Display registration page
    GET /auth/register
    """
    from flask import render_template
    return render_template('auth/register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user account
    POST /auth/register
    Body: {
        "username": "username",
        "email": "user@example.com",
        "password": "Password123",
        "full_name": "Full Name",
        "role": "teacher"  # optional, default: teacher
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Validate input data
        if not is_valid_username(data['username']):
            return jsonify({
                'success': False,
                'message': ERROR_MESSAGES['INVALID_USERNAME'],
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        if not is_valid_email(data['email']):
            return jsonify({
                'success': False,
                'message': ERROR_MESSAGES['INVALID_EMAIL'],
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        if not is_valid_password(data['password']):
            return jsonify({
                'success': False,
                'message': ERROR_MESSAGES['INVALID_PASSWORD'],
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Create user
        user = UserService.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            full_name=data['full_name'],
            role=data.get('role', 'teacher'),
            phone=data.get('phone')
        )
        
        logger.info(f'User registered successfully: {user.username}')
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'data': user.to_dict(),
            'status_code': API_CREATED_CODE
        }), API_CREATED_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error registering user: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Registration failed',
            'status_code': 500
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login_submit():
    """
    Login user (API endpoint and form submission)
    POST /auth/login
    Body (JSON): {
        "username": "username",
        "password": "password"
    }
    Or Form: username, password
    """
    from flask import render_template, redirect, url_for
    
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'username': request.form.get('username'),
                'password': request.form.get('password')
            }
        
        # Validate input
        if not data.get('username') or not data.get('password'):
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Missing username or password',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            else:
                return render_template('auth/login.html', 
                                     error='Vui lòng nhập tên đăng nhập và mật khẩu')
        
        # Authenticate user
        user = UserService.authenticate_user(
            username=data['username'],
            password=data['password']
        )
        
        if not user:
            logger.warning(f'Failed login attempt for user: {data["username"]}')
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Invalid username or password',
                    'status_code': API_UNAUTHORIZED_CODE
                }), API_UNAUTHORIZED_CODE
            else:
                return render_template('auth/login.html',
                                     error='Tên đăng nhập hoặc mật khẩu không đúng')
        
        # For web interface, store in session
        if not request.is_json:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            session.permanent = True  # Make session permanent (respects PERMANENT_SESSION_LIFETIME)
            
            logger.info(f'User logged in successfully (web): {user.username}')
            return redirect(url_for('admin.dashboard'))
        
        # For API, generate JWT token
        token = generate_jwt_token(user)
        if not token:
            return jsonify({
                'success': False,
                'message': 'Failed to generate token',
                'status_code': 500
            }), 500
        
        logger.info(f'User logged in successfully (API): {user.username}')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error logging in: {str(e)}')
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Login failed',
                'status_code': 500
            }), 500
        else:
            return render_template('auth/login.html',
                                 error='Đã xảy ra lỗi khi đăng nhập')

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get current user profile
    GET /auth/profile (requires Authorization header)
    """
    try:
        user = request.current_user
        
        return jsonify({
            'success': True,
            'message': 'Profile retrieved',
            'data': user.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error getting profile: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to get profile',
            'status_code': 500
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Change user password
    POST /auth/change-password
    Body: {
        "old_password": "OldPassword123",
        "new_password": "NewPassword123"
    }
    """
    try:
        data = request.get_json()
        user_id = request.current_user.id
        
        # Validate input
        if not data.get('old_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'message': 'Missing old_password or new_password',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Validate new password strength
        if not is_valid_password(data['new_password']):
            return jsonify({
                'success': False,
                'message': ERROR_MESSAGES['INVALID_PASSWORD'],
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Change password
        user = UserService.change_password(
            user_id=user_id,
            old_password=data['old_password'],
            new_password=data['new_password']
        )
        
        logger.info(f'User changed password: {user.username}')
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error changing password: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to change password',
            'status_code': 500
        }), 500

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Logout user
    GET or POST /auth/logout
    """
    from flask import redirect, url_for
    
    try:
        if 'user_id' in session:
            username = session.get('username', 'Unknown')
            session.clear()
            logger.info(f'User logged out (web): {username}')
        
        if request.is_json or request.method == 'POST':
            return jsonify({
                'success': True,
                'message': 'Logout successful',
                'status_code': API_SUCCESS_CODE
            }), API_SUCCESS_CODE
        else:
            return redirect(url_for('auth.login_page'))
        
    except Exception as e:
        logger.error(f'Error logging out: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Logout failed',
            'status_code': 500
        }), 500

@auth_bp.route('/verify-token', methods=['POST'])
@login_required
def verify_token():
    """
    Verify JWT token
    POST /auth/verify-token (requires Authorization header)
    """
    try:
        user = request.current_user
        
        return jsonify({
            'success': True,
            'message': 'Token is valid',
            'user': user.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error verifying token: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Token verification failed',
            'status_code': API_UNAUTHORIZED_CODE
        }), API_UNAUTHORIZED_CODE
