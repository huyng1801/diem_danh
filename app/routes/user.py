"""
User Routes
Các endpoint quản lý người dùng
"""

from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models.user import User
from app.services.user_service import UserService
from app.utils.decorators import login_required, role_required
from app.utils.validators import is_valid_email, is_valid_password, is_valid_username, is_valid_phone
from app.utils.constants import (
    ERROR_MESSAGES, API_SUCCESS_CODE, API_BAD_REQUEST_CODE,
    API_CREATED_CODE, API_UNAUTHORIZED_CODE, USER_ROLES
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
user_bp = Blueprint('user', __name__, url_prefix='/users')

# ============================================================================
# PAGE ROUTES
# ============================================================================

@user_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def user_list_page():
    """
    User management page
    GET /users/
    """
    return render_template('user/list.html')


@user_bp.route('/create', methods=['GET'])
@login_required
@role_required('admin')
def user_create_page():
    """
    Create user page
    GET /users/create
    """
    return render_template('user/form.html', user=None)


@user_bp.route('/<int:user_id>/edit', methods=['GET'])
@login_required
@role_required('admin')
def user_edit_page(user_id):
    """
    Edit user page
    GET /users/<user_id>/edit
    """
    user = User.query.get_or_404(user_id)
    return render_template('user/form.html', user=user)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@user_bp.route('', methods=['GET'])
@login_required
@role_required('admin')
def list_users():
    """
    Get all users (API endpoint)
    GET /users
    Query params: role (optional), page (optional), limit (optional), search (optional), status (optional)
    """
    try:
        role = request.args.get('role', '').strip()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        
        # Build base query
        query = User.query
        
        # Apply search filter (search in full_name, username, email)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.full_name.ilike(search_pattern),
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )
        
        # Apply role filter
        if role:
            query = query.filter(User.role == role)
        
        # Apply status filter
        if status == 'active':
            query = query.filter(User.is_active == True)
        elif status == 'inactive':
            query = query.filter(User.is_active == False)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Sort by role, then username
        query = query.order_by(User.role.asc(), User.username.asc())
        # Apply pagination
        users = query.offset((page - 1) * limit).limit(limit).all()
        
        # Get current user ID
        current_user = getattr(request, 'current_user', None)
        current_user_id = current_user.id if current_user else None
        
        # Calculate total pages
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return jsonify({
            'success': True,
            'message': 'Users retrieved',
            'data': {
                'users': [u.to_dict() for u in users],
                'current_user_id': current_user_id,
                'pagination': {
                    'page': page,
                    'pages': total_pages,
                    'per_page': limit,
                    'total': total_count
                }
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving users: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve users: {str(e)}',
            'status_code': 500
        }), 500

@user_bp.route('', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    """
    Create new user
    POST /users
    Body: {
        "username": "username",
        "email": "user@example.com",
        "password": "Password123",
        "full_name": "Full Name",
        "role": "teacher"  # teacher, admin, staff
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Validate role
        if data['role'] not in USER_ROLES:
            return jsonify({
                'success': False,
                'message': f'Invalid role. Use: {USER_ROLES}',
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
        
        # Validate phone before sending to service
        if data.get('phone') and data.get('phone').strip():
            if not is_valid_phone(data.get('phone')):
                return jsonify({
                    'success': False,
                    'message': ERROR_MESSAGES['INVALID_PHONE'],
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Create user
        user = UserService.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            full_name=data['full_name'],
            role=data['role'],
            phone=data.get('phone')
        )
        
        logger.info(f'User created by admin: {user.username}')
        
        return jsonify({
            'success': True,
            'message': 'User created',
            'data': user.to_dict(),
            'status_code': API_CREATED_CODE
        }), API_CREATED_CODE
        
    except ValueError as e:
        # Map error messages
        error_msg = str(e)
        if error_msg in ERROR_MESSAGES.values():
            message = error_msg
        elif error_msg in ERROR_MESSAGES:
            message = ERROR_MESSAGES[error_msg]
        else:
            message = error_msg
        
        return jsonify({
            'success': False,
            'message': message,
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error creating user: {str(e)}')
        error_msg = str(e)
        
        # Map common database/validation errors to friendly messages
        error_lower = error_msg.lower()
        if 'unique constraint' in error_lower or 'already exists' in error_lower:
            message = 'Username hoặc email đã tồn tại'
        elif 'foreign key' in error_lower:
            message = 'Dữ liệu tham chiếu không hợp lệ'
        elif 'not null' in error_lower:
            message = 'Vui lòng điền tất cả các trường bắt buộc'
        else:
            message = 'Lỗi tạo người dùng. Vui lòng kiểm tra dữ liệu nhập và thử lại.'
        
        return jsonify({
            'success': False,
            'message': message,
            'status_code': 500
        }), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_user(user_id):
    """
    Get user by ID
    GET /users/<id>
    """
    try:
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'User retrieved',
            'data': user.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving user: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve user: {str(e)}',
            'status_code': 500
        }), 500

@user_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_user(user_id):
    """
    Update user
    PUT /users/<id>
    """
    try:
        data = request.get_json()
        
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }), 404
        
        # Update user
        updated_user = UserService.update_user(user_id, **data)
        
        logger.info(f'User updated: {updated_user.username}')
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'data': updated_user.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        # Map error messages
        error_msg = str(e)
        if error_msg in ERROR_MESSAGES.values():
            message = error_msg
        elif error_msg in ERROR_MESSAGES:
            message = ERROR_MESSAGES[error_msg]
        else:
            message = error_msg
        
        return jsonify({
            'success': False,
            'message': message,
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error updating user: {str(e)}')
        error_msg = str(e)
        
        # Map common database/validation errors to friendly messages
        error_lower = error_msg.lower()
        if 'unique constraint' in error_lower or 'already exists' in error_lower:
            message = 'Email đã tồn tại'
        elif 'foreign key' in error_lower:
            message = 'Dữ liệu tham chiếu không hợp lệ'
        elif 'not null' in error_lower:
            message = 'Vui lòng điền tất cả các trường bắt buộc'
        else:
            message = 'Lỗi cập nhật người dùng. Vui lòng kiểm tra dữ liệu nhập và thử lại.'
        
        return jsonify({
            'success': False,
            'message': message,
            'status_code': 500
        }), 500

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id):
    """
    Delete user
    DELETE /users/<id>
    """
    try:
        from app.models.class_room import ClassRoom
        
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }), 404
        
        # Don't allow deleting the current user
        current_user = getattr(request, 'current_user', None)
        if current_user and current_user.id == user_id:
            return jsonify({
                'success': False,
                'message': 'Cannot delete current user',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Check if user is referenced in classrooms as head teacher
        classrooms_with_user = ClassRoom.query.filter_by(head_teacher_id=user_id).count()
        if classrooms_with_user > 0:
            return jsonify({
                'success': False,
                'message': f'Cannot delete user. User is assigned as head teacher in {classrooms_with_user} class(es). Please reassign or remove from those classes first.',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        UserService.delete_user(user_id)
        
        logger.info(f'User deleted: {user.username}')
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error deleting user: {str(e)}')
        # Parse database error for better message
        error_msg = str(e)
        if 'foreign key constraint' in error_msg.lower():
            return jsonify({
                'success': False,
                'message': 'Cannot delete user. User is referenced in other records. Please check classrooms and other related data.',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        return jsonify({
            'success': False,
            'message': 'Failed to delete user. Please try again.',
            'status_code': 500
        }), 500

@user_bp.route('/<int:user_id>/activate', methods=['POST'])
@login_required
@role_required('admin')
def activate_user(user_id):
    """
    Activate user
    POST /users/<id>/activate
    """
    try:
        user = UserService.activate_user(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }), 404
        
        logger.info(f'User activated: {user.username}')
        
        return jsonify({
            'success': True,
            'message': 'User activated successfully',
            'data': user.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error activating user: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Failed to activate user: {str(e)}',
            'status_code': 500
        }), 500

@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@login_required
@role_required('admin')
def deactivate_user(user_id):
    """
    Deactivate user
    POST /users/<id>/deactivate
    """
    try:
        # Don't allow deactivating the current user
        current_user = getattr(request, 'current_user', None)
        if current_user and current_user.id == user_id:
            return jsonify({
                'success': False,
                'message': 'Cannot deactivate current user',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        user = UserService.deactivate_user(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }), 404
        
        logger.info(f'User deactivated: {user.username}')
        
        return jsonify({
            'success': True,
            'message': 'User deactivated successfully',
            'data': user.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error deactivating user: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Failed to deactivate user: {str(e)}',
            'status_code': 500
        }), 500

@user_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@login_required
@role_required('admin')
def reset_user_password(user_id):
    """
    Reset user password with new password provided
    POST /users/<id>/reset-password
    Body: { "password": "new_password" }
    """
    try:
        # Don't allow resetting own password through this endpoint
        current_user = getattr(request, 'current_user', None)
        if current_user and current_user.id == user_id:
            return jsonify({
                'success': False,
                'message': 'Use profile settings to change your own password',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        data = request.get_json() or {}
        new_password = data.get('password', '').strip()
        
        if not new_password:
            return jsonify({
                'success': False,
                'message': 'Password is required',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }), 404
        
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f'Password reset for user ID: {user_id} by admin')
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error resetting password: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Failed to reset password: {str(e)}',
            'status_code': 500
        }), 500
