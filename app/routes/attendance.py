"""
Attendance Routes
Các endpoint quản lý điểm danh học sinh
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from app import db
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.services.attendance_service import AttendanceService
from app.utils.decorators import login_required, role_required
from app.utils.validators import is_valid_attendance_status, is_valid_session_type
from app.utils.constants import (
    ERROR_MESSAGES, API_SUCCESS_CODE, API_BAD_REQUEST_CODE,
    API_CREATED_CODE, ATTENDANCE_STATUSES, MIN_FACE_CONFIDENCE,
    SESSION_TYPES
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

# ============================================================================
# ROUTES
# ============================================================================

@attendance_bp.route('/record', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def record_attendance():
    """
    Record student attendance
    POST /attendance/record
    Body: {
        "student_id": 1,
        "attendance_log_id": 1,  # Required: ID from start-session
        "status": "present",  # present, absent, late, excused
        "confidence": 0.95  # face recognition confidence (0.0-1.0)
    }
    """
    try:
        from flask import session as flask_session
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'attendance_log_id', 'status']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Validate attendance status
        if not is_valid_attendance_status(data['status']):
            return jsonify({
                'success': False,
                'message': f'Invalid status. Use: {ATTENDANCE_STATUSES}',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Validate confidence if present
        confidence = data.get('confidence', 0.0)
        if confidence:
            confidence = float(confidence)
            if confidence < 0.0 or confidence > 1.0:
                return jsonify({
                    'success': False,
                    'message': 'Confidence must be between 0.0 and 1.0',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Record attendance
        user_id = flask_session.get('user_id')
        attendance = AttendanceService.record_attendance(
            student_id=data['student_id'],
            attendance_log_id=data['attendance_log_id'],
            status=data['status'],
            face_confidence=confidence,
            is_face_recognized=(confidence >= MIN_FACE_CONFIDENCE),
            recorded_by_id=user_id,
            notes=data.get('notes')
        )
        
        logger.info(f'Attendance recorded for student {data["student_id"]} - {data["status"]}')
        
        return jsonify({
            'success': True,
            'message': 'Attendance recorded',
            'data': attendance.to_dict(),
            'status_code': API_CREATED_CODE
        }), API_CREATED_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error recording attendance: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to record attendance',
            'status_code': 500
        }), 500

@attendance_bp.route('/session', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def create_attendance_session():
    """
    Create attendance log for a session
    POST /attendance/session
    Body: {
        "classroom_id": 1,
        "session_date": "2024-01-15",
        "session_type": "morning"  # morning or afternoon
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['classroom_id', 'session_date', 'session_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Validate session type
        if not is_valid_session_type(data['session_type']):
            return jsonify({
                'success': False,
                'message': f'Invalid session type. Use: {SESSION_TYPES}',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Create or get attendance log
        log = AttendanceService.create_or_get_attendance_log(
            classroom_id=data['classroom_id'],
            session_date=datetime.strptime(data['session_date'], '%Y-%m-%d').date(),
            session_type=data['session_type']
        )
        
        logger.info(f'Attendance session created for classroom {data["classroom_id"]}')
        
        return jsonify({
            'success': True,
            'message': 'Attendance session created',
            'data': log.to_dict(),
            'status_code': API_CREATED_CODE
        }), API_CREATED_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error creating attendance session: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to create attendance session',
            'status_code': 500
        }), 500

@attendance_bp.route('/classroom/<int:classroom_id>/date/<date_str>', methods=['GET'])
@login_required
def get_attendance_by_classroom_date(classroom_id, date_str):
    """
    Get all attendance records for classroom on specific date
    GET /attendance/classroom/<id>/date/<YYYY-MM-DD>
    Query params: session_type (optional, morning/afternoon)
    """
    try:
        # Parse date
        try:
            session_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format (use YYYY-MM-DD)',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        session_type = request.args.get('session_type')
        
        # Query attendance records
        query = Attendance.query.filter(
            Attendance.classroom_id == classroom_id,
            Attendance.session_date == session_date
        )
        
        if session_type:
            query = query.filter(Attendance.session_type == session_type)
        
        records = query.all()
        
        return jsonify({
            'success': True,
            'message': 'Attendance records retrieved',
            'data': [r.to_dict() for r in records],
            'total': len(records),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving attendance: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve attendance',
            'status_code': 500
        }), 500

@attendance_bp.route('/<int:attendance_id>', methods=['GET'])
@login_required
def get_attendance(attendance_id):
    """
    Get attendance record by ID
    GET /attendance/<id>
    """
    try:
        attendance = Attendance.query.get(attendance_id)
        
        if not attendance:
            return jsonify({
                'success': False,
                'message': 'Attendance record not found',
                'status_code': 404
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Attendance record retrieved',
            'data': attendance.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving attendance: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve attendance',
            'status_code': 500
        }), 500

@attendance_bp.route('/<int:attendance_id>', methods=['PUT'])
@login_required
@role_required('teacher', 'admin')
def update_attendance(attendance_id):
    """
    Update attendance record
    PUT /attendance/<id>
    Body: {
        "status": "present",  # present, absent, late, excused
        "notes": "Sick"
    }
    """
    try:
        attendance = Attendance.query.get(attendance_id)
        
        if not attendance:
            return jsonify({
                'success': False,
                'message': 'Attendance record not found',
                'status_code': 404
            }), 404
        
        data = request.get_json()
        
        # Validate status if provided
        if 'status' in data:
            if not is_valid_attendance_status(data['status']):
                return jsonify({
                    'success': False,
                    'message': f'Invalid status. Use: {ATTENDANCE_STATUSES}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            
            attendance.status = data['status']
        
        # Update notes if provided
        if 'notes' in data:
            attendance.notes = data['notes']
        
        attendance.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'Attendance record updated: {attendance_id}')
        
        return jsonify({
            'success': True,
            'message': 'Attendance record updated',
            'data': attendance.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating attendance: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to update attendance',
            'status_code': 500
        }), 500

@attendance_bp.route('/student/<int:student_id>/history', methods=['GET'])
@login_required
def get_student_attendance_history(student_id):
    """
    Get attendance history for student
    GET /attendance/student/<id>/history
    Query params: page (optional), limit (optional), from_date (optional), to_date (optional)
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Build query
        query = Attendance.query.filter_by(student_id=student_id)
        
        # Filter by date range if provided
        if from_date:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.session_date >= from_date_obj)
        
        if to_date:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.session_date <= to_date_obj)
        
        records = query.order_by(Attendance.session_date.desc()).all()
        
        # Pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = records[start:end]
        
        return jsonify({
            'success': True,
            'message': 'Attendance history retrieved',
            'data': [r.to_dict() for r in paginated],
            'total': len(records),
            'page': page,
            'limit': limit,
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error retrieving attendance history: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve attendance history',
            'status_code': 500
        }), 500

@attendance_bp.route('/auto-mark-absent', methods=['POST'])
@login_required
@role_required('admin')
def auto_mark_absent():
    """
    Auto-mark absent for unrecorded attendance
    POST /attendance/auto-mark-absent
    Body: {
        "classroom_id": 1,
        "session_date": "2024-01-15",
        "session_type": "morning"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['classroom_id', 'session_date', 'session_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Parse date
        session_date = datetime.strptime(data['session_date'], '%Y-%m-%d').date()
        
        # Mark absent
        count = AttendanceService.mark_absent_unrecorded(
            classroom_id=data['classroom_id'],
            session_date=session_date,
            session_type=data['session_type']
        )
        
        logger.info(f'Auto-marked {count} students absent')
        
        return jsonify({
            'success': True,
            'message': f'Auto-marked {count} students as absent',
            'data': {'count': count},
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error auto-marking absent: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to auto-mark absent',
            'status_code': 500
        }), 500

@attendance_bp.route('/finalize', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def finalize_attendance_session():
    """
    Finalize attendance session (lock and calculate stats)
    POST /attendance/finalize
    Body: {
        "attendance_log_id": 1
    }
    """
    try:
        data = request.get_json()
        log_id = data.get('attendance_log_id')
        
        if not log_id:
            return jsonify({
                'success': False,
                'message': 'Missing attendance_log_id',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        log = AttendanceLog.query.get(log_id)
        
        if not log:
            return jsonify({
                'success': False,
                'message': 'Attendance log not found',
                'status_code': 404
            }), 404
        
        # Finalize
        log = AttendanceService.finalize_attendance_log(log_id)
        
        logger.info(f'Attendance session finalized: {log_id}')
        
        return jsonify({
            'success': True,
            'message': 'Attendance session finalized',
            'data': log.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error finalizing attendance: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to finalize attendance',
            'status_code': 500
        }), 500

@attendance_bp.route('/classroom/<int:classroom_id>/summary', methods=['GET'])
@login_required
def get_classroom_attendance_summary(classroom_id):
    """
    Get attendance summary for classroom
    GET /attendance/classroom/<id>/summary
    Query params: from_date, to_date (optional)
    """
    try:
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Build query
        query = Attendance.query.filter_by(classroom_id=classroom_id)
        
        if from_date:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.session_date >= from_date_obj)
        
        if to_date:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.session_date <= to_date_obj)
        
        records = query.all()
        
        # Calculate summary
        total = len(records)
        present_count = len([r for r in records if r.status == 'present'])
        absent_count = len([r for r in records if r.status == 'absent'])
        late_count = len([r for r in records if r.status == 'late'])
        excused_count = len([r for r in records if r.status == 'excused'])
        
        return jsonify({
            'success': True,
            'message': 'Attendance summary retrieved',
            'data': {
                'classroom_id': classroom_id,
                'total_records': total,
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'excused': excused_count,
                'present_percentage': (present_count / total * 100) if total > 0 else 0
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error retrieving attendance summary: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve attendance summary',
            'status_code': 500
        }), 500


@attendance_bp.route('/start-session', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def start_attendance_session():
    """
    Start attendance session and create log
    POST /attendance/start-session
    Body: {
        "classroom_id": 1,
        "session_date": "2024-01-15",
        "session_type": "morning"
    }
    """
    try:
        from flask import session as flask_session
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['classroom_id', 'session_date', 'session_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Validate session type
        if not is_valid_session_type(data['session_type']):
            return jsonify({
                'success': False,
                'message': f'Invalid session type. Use: {SESSION_TYPES}',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Parse date
        session_date = datetime.strptime(data['session_date'], '%Y-%m-%d').date()
        
        # Create or get attendance log
        user_id = flask_session.get('user_id')
        log = AttendanceService.create_or_get_attendance_log(
            classroom_id=data['classroom_id'],
            session_date=session_date,
            session_type=data['session_type'],
            start_time=datetime.now(),
            recorded_by_id=user_id
        )
        
        logger.info(f'Attendance session started: {log.id}')
        
        return jsonify({
            'success': True,
            'message': 'Attendance session started',
            'data': {
                'log_id': log.id,
                'classroom_id': log.classroom_id,
                'session_date': log.session_date.isoformat(),
                'session_type': log.session_type,
                'start_time': log.start_time.isoformat()
            },
            'status_code': API_CREATED_CODE
        }), API_CREATED_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error starting attendance session: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to start attendance session',
            'status_code': 500
        }), 500


@attendance_bp.route('/stop-session', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def stop_attendance_session():
    """
    Stop attendance session and finalize
    POST /attendance/stop-session
    Body: {
        "log_id": 1
    }
    """
    try:
        data = request.get_json()
        log_id = data.get('log_id')
        
        if not log_id:
            return jsonify({
                'success': False,
                'message': 'Missing log_id',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        log = AttendanceLog.query.get(log_id)
        
        if not log:
            return jsonify({
                'success': False,
                'message': 'Attendance log not found',
                'status_code': 404
            }), 404
        
        # Set end time
        log.end_time = datetime.now()
        
        # Calculate statistics
        log.calculate_statistics()
        
        # Finalize
        log.is_finalized = True
        log.updated_at = datetime.now()
        
        db.session.commit()
        
        logger.info(f'Attendance session stopped: {log_id}')
        
        return jsonify({
            'success': True,
            'message': 'Attendance session stopped',
            'data': log.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error stopping attendance session: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to stop attendance session',
            'status_code': 500
        }), 500


# ============================================================================
# PAGE ROUTES (Render Templates)
# ============================================================================

@attendance_bp.route('/camera', methods=['GET'])
@login_required
@role_required('teacher', 'admin')
def camera():
    """
    Attendance camera page for face recognition
    GET /attendance/camera
    """
    from flask import render_template
    return render_template('attendance/camera.html')


@attendance_bp.route('/view-result', methods=['GET'])
@login_required
def view_result():
    """
    View attendance results page
    GET /attendance/view-result
    """
    from flask import render_template
    from app.models.attendance_log import AttendanceLog
    from app.models.attendance import Attendance
    from app.models.class_room import ClassRoom
    
    try:
        # Get the latest attendance session or from query parameter
        session_id = request.args.get('session_id', type=int)
        
        if session_id:
            session = AttendanceLog.query.get(session_id)
        else:
            # Get the latest session
            session = AttendanceLog.query.order_by(AttendanceLog.created_at.desc()).first()
        
        if not session:
            return render_template('attendance/view_result.html', 
                                 session_data=None,
                                 attendance_records=[],
                                 statistics={},
                                 recognition_stats={})
        
        # Get attendance records for this session
        records = Attendance.query.filter_by(attendance_log_id=session.id).all()
        
        # Build session data dict
        classroom = session.classroom if session.classroom else ClassRoom()
        session_data = {
            'id': session.id,
            'class_name': classroom.class_name if classroom else 'N/A',
            'teacher_name': session.recorded_by.full_name if session.recorded_by else 'N/A',
            'classroom': f"Phòng {classroom.room_number}" if classroom and classroom.room_number else 'N/A',
            'date': session.session_date,
            'session_type_display': 'Sáng' if session.session_type == 'morning' else 'Chiều',
            'start_time': session.start_time,
            'end_time': session.end_time,
            'is_completed': session.is_finalized,
            'notes': '',  # Will be loaded from database
            'updated_at': session.updated_at,
            'duration': f"{(session.end_time - session.start_time).seconds // 60} phút" if session.end_time else 'Chưa kết thúc'
        }
        
        # Get total active students from classroom
        from app.models.student import Student
        total_students = db.session.query(Student).filter_by(
            classroom_id=classroom.id,
            is_active=True
        ).count()
        
        # Build attendance records
        attendance_records = []
        auto_count = 0
        manual_count = 0
        confidence_values = []
        
        for record in records:
            student = record.student
            if not student:
                continue
            
            # Get avatar: prefer avatar_url, fallback to first student_image
            student_avatar = student.avatar_url
            if not student_avatar:
                # Get first valid student image
                from app.models.student_image import StudentImage
                first_image = db.session.query(StudentImage).filter_by(
                    student_id=student.id,
                    is_valid=True
                ).first()
                student_avatar = first_image.image_url if first_image else None
            
            attendance_records.append({
                'id': record.id,
                'student_code': student.student_code,
                'student_name': student.full_name,
                'student_avatar': student_avatar,
                'status': record.status,
                'check_in_time': record.check_in_time,
                'confidence': record.face_confidence,
                'is_manual': not record.is_face_recognized,
                'snapshot_url': record.check_in_image_url
            })
            
            if record.is_face_recognized:
                auto_count += 1
                if record.face_confidence:
                    confidence_values.append(record.face_confidence)
            else:
                manual_count += 1
        
        # Calculate statistics - use actual total_students from classroom
        statistics = {
            'present_count': len([r for r in records if r.status == 'present']),
            'absent_count': total_students - len([r for r in records if r.status == 'present']),
            'late_count': len([r for r in records if r.status == 'late']),
            'total_students': total_students,
            'attendance_rate': (len([r for r in records if r.status == 'present']) / total_students * 100) if total_students > 0 else 0
        }
        
        # Calculate recognition statistics
        avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
        high_conf = len([c for c in confidence_values if c >= 0.9])
        med_conf = len([c for c in confidence_values if 0.7 <= c < 0.9])
        low_conf = len([c for c in confidence_values if c < 0.7])
        
        recognition_stats = {
            'auto_count': auto_count,
            'manual_count': manual_count,
            'avg_confidence': f"{avg_confidence * 100:.1f}" if confidence_values else '0',
            'avg_processing_time': '125',  # Default value
            'high_confidence_count': high_conf,
            'high_confidence_pct': (high_conf / len(confidence_values) * 100) if confidence_values else 0,
            'medium_confidence_count': med_conf,
            'medium_confidence_pct': (med_conf / len(confidence_values) * 100) if confidence_values else 0,
            'low_confidence_count': low_conf,
            'low_confidence_pct': (low_conf / len(confidence_values) * 100) if confidence_values else 0
        }
        
        return render_template('attendance/view_result.html',
                             session_data=session_data,
                             attendance_records=attendance_records,
                             statistics=statistics,
                             recognition_stats=recognition_stats)
    
    except Exception as e:
        logger.error(f"Error in view_result: {str(e)}")
        return render_template('attendance/view_result.html',
                             session_data=None,
                             attendance_records=[],
                             statistics={},
                             recognition_stats={})


@attendance_bp.route('/history', methods=['GET'])
@login_required
def history():
    """
    Attendance history page
    GET /attendance/history
    """
    from flask import render_template
    return render_template('attendance/history.html')


@attendance_bp.route('/api/history', methods=['GET'])
@login_required
def get_attendance_history():
    """
    Get attendance history (API)
    GET /attendance/api/history
    Query params: class_id, session_type, status, from_date, to_date, search, sort_by, page, page_size
    """
    try:
        # Get query parameters
        class_id = request.args.get('class_id', type=int)
        session_type = request.args.get('session_type', '').strip()
        status = request.args.get('status', '').strip()
        from_date = request.args.get('from_date', '').strip()
        to_date = request.args.get('to_date', '').strip()
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'date_desc').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 25, type=int)
        
        from app.models.class_room import ClassRoom
        from app.models.user import User
        
        # Build query
        query = db.session.query(AttendanceLog).join(ClassRoom)
        
        # Apply filters
        if class_id:
            query = query.filter(AttendanceLog.classroom_id == class_id)
        
        if session_type:
            query = query.filter(AttendanceLog.session_type == session_type)
        
        if status == 'completed':
            query = query.filter(AttendanceLog.is_finalized == True)
        elif status == 'in-progress':
            query = query.filter(AttendanceLog.is_finalized == False)
        
        if from_date:
            query = query.filter(AttendanceLog.session_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
        
        if to_date:
            query = query.filter(AttendanceLog.session_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
        
        if search:
            query = query.filter(
                db.or_(
                    ClassRoom.class_name.ilike(f'%{search}%'),
                    ClassRoom.grade.ilike(f'%{search}%')
                )
            )
        
        # Apply sorting
        if sort_by == 'date_desc':
            query = query.order_by(AttendanceLog.session_date.desc(), AttendanceLog.created_at.desc())
        elif sort_by == 'date_asc':
            query = query.order_by(AttendanceLog.session_date.asc(), AttendanceLog.created_at.asc())
        elif sort_by == 'class_name':
            query = query.order_by(ClassRoom.class_name.asc())
        elif sort_by == 'attendance_rate':
            query = query.order_by(AttendanceLog.present_count.desc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        sessions = query.offset(offset).limit(page_size).all()
        
        # Convert to dict
        sessions_data = []
        for session in sessions:
            classroom = session.classroom
            teacher = session.recorded_by
            
            # Get accurate total students from classroom (not from attendance_logs)
            from app.models.student import Student
            total_students = db.session.query(Student).filter_by(
                classroom_id=classroom.id,
                is_active=True
            ).count()
            
            sessions_data.append({
                'id': session.id,
                'date': session.session_date.isoformat(),
                'session_type': session.session_type,
                'class_name': classroom.class_name,
                'grade': classroom.grade,
                'teacher_name': teacher.full_name if teacher else 'N/A',
                'teacher_title': teacher.role_display if teacher else '',
                'total_students': total_students,  # Get from Student table
                'present_count': session.present_count,
                'absent_count': session.absent_count,
                'late_count': session.late_count,
                'attendance_rate': round((session.present_count / total_students * 100) if total_students > 0 else 0, 1),
                'status': 'completed' if session.is_finalized else 'in-progress',
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration': calculate_duration(session.start_time, session.end_time),
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat() if session.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': sessions_data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        })
        
    except Exception as e:
        logger.error(f'Error getting attendance history: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to load attendance history'
        }), 500


def calculate_duration(start_time, end_time):
    """Calculate duration between start and end time"""
    if not start_time or not end_time:
        return None
    
    delta = end_time - start_time
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if hours > 0:
        return f'{hours}h {minutes}m'
    return f'{minutes}m'


@attendance_bp.route('/edit-result', methods=['GET'])
@login_required
@role_required('teacher', 'admin')
def edit_result():
    """
    Edit attendance results page
    GET /attendance/edit-result
    """
    from flask import render_template
    return render_template('attendance/edit_result.html')
