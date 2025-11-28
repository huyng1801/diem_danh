"""
Admin Routes
Các endpoint quản trị hệ thống
"""

from flask import Blueprint, request, jsonify, render_template
from app import db
from app.utils.decorators import login_required, role_required
import logging

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================================================
# ROUTES
# ============================================================================

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """
    Admin dashboard page
    GET /admin/dashboard
    """
    # Get current user from request (set by login_required decorator)
    current_user = getattr(request, 'current_user', None)
    
    return render_template('admin/dashboard.html', current_user=current_user)


@admin_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """
    Get system statistics
    GET /admin/stats
    """
    try:
        from app.models.student import Student
        from app.models.user import User
        from app.models.class_room import ClassRoom
        from app.models.attendance import Attendance
        from app.models.attendance_log import AttendanceLog
        
        # Count total records
        total_students = db.session.query(db.func.count(Student.id)).scalar() or 0
        active_students = db.session.query(db.func.count(Student.id)).filter_by(is_active=True).scalar() or 0
        
        total_users = db.session.query(db.func.count(User.id)).scalar() or 0
        active_users = db.session.query(db.func.count(User.id)).filter_by(is_active=True).scalar() or 0
        teachers = db.session.query(db.func.count(User.id)).filter_by(role='teacher', is_active=True).scalar() or 0
        admins = db.session.query(db.func.count(User.id)).filter_by(role='admin', is_active=True).scalar() or 0
        
        total_classrooms = db.session.query(db.func.count(ClassRoom.id)).scalar() or 0
        active_classrooms = db.session.query(db.func.count(ClassRoom.id)).filter_by(is_active=True).scalar() or 0
        
        total_attendance = db.session.query(db.func.count(Attendance.id)).scalar() or 0
        total_sessions = db.session.query(db.func.count(AttendanceLog.id)).scalar() or 0
        
        # Count students with face recognition
        face_enabled = db.session.query(db.func.count(Student.id)).filter_by(face_recognition_enabled=True).scalar() or 0
        
        stats = {
            'students': total_students,
            'active_students': active_students,
            'face_enabled_students': face_enabled,
            'users': {
                'total': total_users,
                'active': active_users,
                'teachers': teachers,
                'admins': admins
            },
            'classrooms': total_classrooms,
            'active_classrooms': active_classrooms,
            'attendance_records': total_attendance,
            'attendance_sessions': total_sessions
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Lỗi khi lấy thống kê'
        }), 500


@admin_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """
    Get users list with optional filtering
    GET /admin/users?role=teacher&status=active
    """
    try:
        from app.models.user import User
        
        # Get query parameters
        role = request.args.get('role', None)
        status = request.args.get('status', None)
        
        # Build query
        query = db.session.query(User)
        
        if role:
            query = query.filter_by(role=role)
        
        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)
        
        # Order by created_at desc
        query = query.order_by(User.created_at.desc())
        
        users = query.all()
        
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_active': user.is_active,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in users]
        
        return jsonify({
            'success': True,
            'data': users_data
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Lỗi khi lấy danh sách người dùng'
        }), 500


