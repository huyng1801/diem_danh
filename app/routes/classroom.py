"""
Classroom Routes
Các endpoint quản lý lớp học
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models.class_room import ClassRoom
from app.services.classroom_service import ClassRoomService
from app.models.student import Student
from app.utils.decorators import login_required, role_required
from app.utils.constants import (
    ERROR_MESSAGES, API_SUCCESS_CODE, API_BAD_REQUEST_CODE,
    API_CREATED_CODE, MAX_STUDENTS_PER_CLASS, ALLOWED_GRADES
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
classroom_bp = Blueprint('classroom', __name__, url_prefix='/classroom')

# ============================================================================
# ROUTES
# ============================================================================

@classroom_bp.route('/', methods=['GET'], endpoint='index')
@classroom_bp.route('/list', methods=['GET'], endpoint='list')
@login_required
def list_classrooms():
    """
    List classrooms page
    GET /classroom or /classroom/list
    """
    try:
        from flask import render_template
        return render_template('classroom/list.html')
    except Exception as e:
        logger.error(f'Error rendering classroom list: {str(e)}')
        return render_template('classroom/list.html')

@classroom_bp.route('/api/list', methods=['GET'])
@login_required
def list_classrooms_api():
    """
    Get all classrooms (API endpoint)
    GET /classroom/api/list
    Query params: search, grade, status, page, limit
    """
    try:
        # Get filter parameters
        search = request.args.get('search', '').strip()
        grade = request.args.get('grade', '').strip()
        status = request.args.get('status', '').strip()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        from app.models.class_room import ClassRoom
        from app.models.user import User
        
        # Start with base query
        query = ClassRoom.query
        
        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    ClassRoom.class_name.ilike(f'%{search}%'),
                    ClassRoom.head_teacher.ilike(f'%{search}%'),
                    ClassRoom.room_number.ilike(f'%{search}%')
                )
            )
        
        # Apply grade filter
        if grade:
            query = query.filter(ClassRoom.grade == grade)
            
        # Apply status filter
        if status:
            is_active = status == 'active'
            query = query.filter(ClassRoom.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        # Apply pagination
        offset = (page - 1) * limit
        classrooms = query.order_by(ClassRoom.created_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to dict with additional info
        classrooms_data = []
        for classroom in classrooms:
            classroom_dict = {
                'id': classroom.id,
                'class_name': classroom.class_name,
                'grade': classroom.grade,
                'room_number': classroom.room_number,
                'head_teacher': classroom.head_teacher,
                'head_teacher_id': classroom.head_teacher_id,
                'academic_year_id': classroom.academic_year_id,
                'student_count': classroom.student_count or 0,
                'max_student': classroom.max_student or 45,
                'is_active': classroom.is_active,
                'created_at': classroom.created_at.isoformat() if classroom.created_at else None,
                'updated_at': classroom.updated_at.isoformat() if classroom.updated_at else None
            }
            classrooms_data.append(classroom_dict)
        
        return jsonify({
            'success': True,
            'message': 'Danh sách lớp học được tải thành công',
            'data': {
                'classrooms': classrooms_data,
                'pagination': {
                    'total': total,
                    'pages': total_pages,
                    'current_page': page,
                    'limit': limit,
                    'has_next': (page * limit) < total,
                    'has_prev': page > 1
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error retrieving classrooms: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi tải danh sách lớp học',
            'error': str(e)
        }), 500

@classroom_bp.route('/<int:classroom_id>', methods=['GET'])
@login_required
def get_classroom(classroom_id):
    """
    View classroom detail page
    GET /classroom/<id>
    """
    try:
        from app.models.class_room import ClassRoom
        from app.models.user import User
        from app.models.academic_year import AcademicYear
        
        # Get classroom with relationships
        classroom = ClassRoom.query.options(
            db.joinedload(ClassRoom.academic_year),
            db.joinedload(ClassRoom.head_teacher_obj)
        ).get(classroom_id)
        
        if not classroom:
            return render_template('error.html', message='Không tìm thấy lớp học'), 404
        
        # Prepare classroom data for template
        class_data = {
            'id': classroom.id,
            'class_name': classroom.class_name,
            'grade': classroom.grade,
            'room_number': classroom.room_number,
            'head_teacher': classroom.head_teacher,
            'head_teacher_obj': classroom.head_teacher_obj,
            'academic_year_id': classroom.academic_year_id,
            'student_count': classroom.student_count or 0,
            'max_student': classroom.max_student or 45,
            'is_active': classroom.is_active,
            'created_at': classroom.created_at,
            'updated_at': classroom.updated_at
        }
        
        return render_template('classroom/detail.html', class_data=class_data)
        
    except Exception as e:
        logger.error(f'Error retrieving classroom: {str(e)}')
        return render_template('error.html', message='Lỗi khi tải thông tin lớp học'), 500

@classroom_bp.route('/<int:classroom_id>/students', methods=['GET'])
@login_required
def get_classroom_students(classroom_id):
    """
    Get all students in classroom
    GET /classroom/<id>/students
    Query params: page (optional), limit (optional)
    """
    try:
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        students = ClassRoomService.get_classroom_students(classroom_id)
        
        # Pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = students[start:end]
        
        return jsonify({
            'success': True,
            'message': 'Classroom students retrieved',
            'data': [s.to_dict() for s in paginated],
            'total': len(students),
            'page': page,
            'limit': limit,
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving classroom students: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve classroom students',
            'status_code': 500
        }), 500

@classroom_bp.route('/<int:classroom_id>/add-student', methods=['POST'])
@login_required
@role_required('admin')
def add_student_to_classroom(classroom_id):
    """
    Add student to classroom
    POST /classroom/<id>/add-student
    Body: {
        "student_id": 1
    }
    """
    try:
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({
                'success': False,
                'message': 'Missing student_id',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Check if classroom is full
        if ClassRoomService.is_classroom_full(classroom_id):
            return jsonify({
                'success': False,
                'message': f'Classroom is full (max {MAX_STUDENTS_PER_CLASS} students)',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Add student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found',
                'status_code': 404
            }), 404
        
        student.classroom_id = classroom_id
        db.session.commit()
        
        logger.info(f'Student {student_id} added to classroom {classroom_id}')
        
        return jsonify({
            'success': True,
            'message': 'Student added to classroom',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error adding student to classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to add student to classroom',
            'status_code': 500
        }), 500

@classroom_bp.route('/<int:classroom_id>/remove-student', methods=['POST'])
@login_required
@role_required('admin')
def remove_student_from_classroom(classroom_id):
    """
    Remove student from classroom
    POST /classroom/<id>/remove-student
    Body: {
        "student_id": 1
    }
    """
    try:
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({
                'success': False,
                'message': 'Missing student_id',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Remove student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found',
                'status_code': 404
            }), 404
        
        student.classroom_id = None
        db.session.commit()
        
        logger.info(f'Student {student_id} removed from classroom {classroom_id}')
        
        return jsonify({
            'success': True,
            'message': 'Student removed from classroom',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error removing student from classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to remove student from classroom',
            'status_code': 500
        }), 500

@classroom_bp.route('/api/<int:classroom_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_classroom_api(classroom_id):
    """
    Update classroom (API)
    PUT /classroom/api/<id>
    Body: {
        "class_name": "6A1",
        "grade": "6",
        "room_number": "A101",
        "head_teacher_id": 1,
        "max_student": 45,
        "is_active": true
    }
    """
    try:
        from app.models.class_room import ClassRoom
        classroom = ClassRoom.query.get(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy lớp học'
            }), 404
        
        data = request.get_json()
        
        # Validate grade if provided
        if 'grade' in data:
            if str(data['grade']) not in ALLOWED_GRADES:
                return jsonify({
                    'success': False,
                    'message': f'Khối học không hợp lệ. Cho phép: {", ".join(ALLOWED_GRADES)}'
                }), 400
        
        # Check if classroom name exists in the same academic year (excluding current classroom)
        if 'class_name' in data:
            existing = ClassRoom.query.filter(
                ClassRoom.class_name == data['class_name'],
                ClassRoom.academic_year_id == classroom.academic_year_id,
                ClassRoom.id != classroom_id
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'Tên lớp "{data["class_name"]}" đã tồn tại trong niên khóa này'
                }), 400
        
        # Update fields
        if 'class_name' in data:
            classroom.class_name = data['class_name']
        if 'grade' in data:
            classroom.grade = str(data['grade'])
        if 'room_number' in data:
            classroom.room_number = data['room_number']
        if 'head_teacher_id' in data:
            classroom.head_teacher_id = data['head_teacher_id']
        if 'max_student' in data:
            classroom.max_student = data['max_student']
        if 'is_active' in data:
            classroom.is_active = data['is_active']
        
        classroom.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'Classroom updated: {classroom.class_name}')
        
        return jsonify({
            'success': True,
            'message': 'Cập nhật lớp học thành công',
            'data': {
                'id': classroom.id,
                'class_name': classroom.class_name,
                'grade': classroom.grade,
                'room_number': classroom.room_number,
                'head_teacher': classroom.head_teacher,
                'head_teacher_id': classroom.head_teacher_id,
                'academic_year_id': classroom.academic_year_id,
                'student_count': classroom.student_count,
                'max_student': classroom.max_student,
                'is_active': classroom.is_active,
                'created_at': classroom.created_at.isoformat() if classroom.created_at else None,
                'updated_at': classroom.updated_at.isoformat() if classroom.updated_at else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi cập nhật lớp học',
            'error': str(e)
        }), 500

@classroom_bp.route('/api/<int:classroom_id>/delete', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_classroom_api(classroom_id):
    """
    Delete classroom (API)
    DELETE /classroom/api/<id>/delete
    """
    try:
        from app.models.class_room import ClassRoom
        classroom = ClassRoom.query.get(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy lớp học'
            }), 404
        
        # Check if classroom has students
        if classroom.student_count and classroom.student_count > 0:
            return jsonify({
                'success': False,
                'message': 'Không thể xóa lớp học đã có học sinh. Vui lòng chuyển học sinh sang lớp khác trước.'
            }), 400
        
        classroom_name = classroom.class_name
        db.session.delete(classroom)
        db.session.commit()
        
        logger.info(f'Classroom deleted: {classroom_name}')
        
        return jsonify({
            'success': True,
            'message': 'Xóa lớp học thành công'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi xóa lớp học',
            'error': str(e)
        }), 500

@classroom_bp.route('/api/students/<int:classroom_id>', methods=['GET'])
@login_required
def get_classroom_students_api(classroom_id):
    """
    Get students in a classroom (API)
    GET /classroom/api/students/<id>
    """
    try:
        from app.models.student import Student
        
        # Check if classroom exists
        classroom = ClassRoom.query.get(classroom_id)
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy lớp học'
            }), 404
        
        # Get students in this classroom
        students = Student.query.filter_by(class_room_id=classroom_id).all()
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'full_name': student.full_name,
                'student_code': student.student_code,
                'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                'gender': student.gender,
                'created_at': student.created_at.isoformat() if hasattr(student, 'created_at') and student.created_at else None
            })
        
        return jsonify({
            'success': True,
            'message': 'Tải danh sách học sinh thành công',
            'data': students_data,
            'total': len(students_data)
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting classroom students: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi tải danh sách học sinh',
            'error': str(e)
        }), 500

@classroom_bp.route('/api/academic_years', methods=['GET'])
@login_required
def get_academic_years_api():
    """
    Get all academic years for form select options
    GET /classroom/api/academic_years
    """
    try:
        from app.models.academic_year import AcademicYear
        
        academic_years = AcademicYear.query.filter_by(is_active=True).all()
        
        data = []
        for year in academic_years:
            data.append({
                'id': year.id,
                'name': year.year,
                'year': year.year,
                'start_date': year.start_date.isoformat() if year.start_date else None,
                'end_date': year.end_date.isoformat() if year.end_date else None,
                'is_current': year.is_active,
                'is_active': year.is_active
            })
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting academic years: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi tải niên khóa',
            'error': str(e)
        }), 500

@classroom_bp.route('/api/teachers', methods=['GET'])
@login_required
def get_teachers_api():
    """
    Get all teachers for form select options
    GET /classroom/api/teachers
    """
    try:
        from app.models.user import User
        
        teachers = User.query.filter_by(role='teacher', is_active=True).all()
        
        data = []
        for teacher in teachers:
            data.append({
                'id': teacher.id,
                'full_name': teacher.full_name,
                'email': teacher.email,
                'phone': teacher.phone
            })
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting teachers: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi tải danh sách giáo viên',
            'error': str(e)
        }), 500

@classroom_bp.route('/<int:classroom_id>/count', methods=['GET'])
@login_required
def count_classroom_students(classroom_id):
    """
    Get student count in classroom
    GET /classroom/<id>/count
    """
    try:
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        count = ClassRoomService.get_classroom_student_count(classroom_id)
        
        return jsonify({
            'success': True,
            'message': 'Student count retrieved',
            'data': {
                'classroom_id': classroom_id,
                'count': count,
                'max': MAX_STUDENTS_PER_CLASS
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error counting classroom students: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to count classroom students',
            'status_code': 500
        }), 500


# ============================================================================
# PAGE ROUTES (Render Templates)
# ============================================================================

@classroom_bp.route('/form', methods=['GET'])
@login_required
@role_required('admin')
def form():
    """
    Classroom form page (create new classroom)
    GET /classroom/form
    """
    return render_template('classroom/form.html')

@classroom_bp.route('/edit/<int:classroom_id>', methods=['GET'])
@login_required
@role_required('admin')
def edit_classroom_page(classroom_id):
    """
    Edit classroom page
    GET /classroom/edit/<id>
    """
    try:
        from app.models.class_room import ClassRoom
        classroom = ClassRoom.query.get(classroom_id)
        
        if not classroom:
            return render_template('error.html', message='Không tìm thấy lớp học'), 404
        
        return render_template('classroom/form.html', class_data=classroom)
        
    except Exception as e:
        logger.error(f'Error retrieving classroom for edit: {str(e)}')
        return render_template('error.html', message='Lỗi khi tải thông tin lớp học'), 500

@classroom_bp.route('/detail/<int:classroom_id>', methods=['GET'])
@login_required
def detail_classroom_page(classroom_id):
    """
    Classroom detail page
    GET /classroom/detail/<id>
    """
    try:
        from app.models.class_room import ClassRoom
        classroom = ClassRoom.query.get(classroom_id)
        
        if not classroom:
            return render_template('error.html', message='Không tìm thấy lớp học'), 404
        
        return render_template('classroom/detail.html', class_data=classroom)
        
    except Exception as e:
        logger.error(f'Error retrieving classroom detail: {str(e)}')
        return render_template('error.html', message='Lỗi khi tải thông tin lớp học'), 500

# ============================================================================
# API ROUTES (Return JSON)
# ============================================================================

@classroom_bp.route('/api/get/<int:classroom_id>', methods=['GET'])
@login_required
def get_classroom_api(classroom_id):
    """
    Get classroom by ID (API)
    GET /classroom/api/get/<id>
    """
    try:
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Classroom retrieved',
            'data': classroom.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve classroom',
            'status_code': 500
        }), 500

@classroom_bp.route('/api/create', methods=['POST'])
@login_required
@role_required('admin')
def create_classroom_api():
    """
    Create new classroom (API)
    POST /classroom/api/create
    Body: {
        "class_name": "6A1",
        "grade": "6",
        "academic_year_id": 1,
        "room_number": "A101",
        "head_teacher": "Nguyễn Văn A",
        "head_teacher_id": 1,
        "max_student": 45,
        "is_active": true
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['class_name', 'grade', 'academic_year_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Trường {field} là bắt buộc'
                }), 400
        
        # Validate that either head_teacher_id or head_teacher is provided
        if not data.get('head_teacher_id') and not data.get('head_teacher'):
            return jsonify({
                'success': False,
                'message': 'Vui lòng chọn giáo viên chủ nhiệm'
            }), 400
        
        # Validate grade
        if str(data['grade']) not in ALLOWED_GRADES:
            return jsonify({
                'success': False,
                'message': f'Khối học không hợp lệ. Cho phép: {", ".join(ALLOWED_GRADES)}'
            }), 400
        
        # Check if classroom name exists in the same academic year
        from app.models.class_room import ClassRoom
        existing = ClassRoom.query.filter_by(
            class_name=data['class_name'],
            academic_year_id=data['academic_year_id']
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': f'Tên lớp "{data["class_name"]}" đã tồn tại trong niên khóa này'
            }), 400
        
        # Create classroom
        classroom = ClassRoom(
            class_name=data['class_name'],
            grade=str(data['grade']),
            academic_year_id=data['academic_year_id'],
            room_number=data.get('room_number'),
            head_teacher_id=data.get('head_teacher_id') if data.get('head_teacher_id') else None,
            head_teacher=data.get('head_teacher') if data.get('head_teacher') else None,
            max_student=data.get('max_student', 45),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(classroom)
        db.session.commit()
        
        logger.info(f'Classroom created: {classroom.class_name}')
        
        return jsonify({
            'success': True,
            'message': 'Tạo lớp học thành công',
            'data': {
                'id': classroom.id,
                'class_name': classroom.class_name,
                'grade': classroom.grade,
                'room_number': classroom.room_number,
                'head_teacher': classroom.head_teacher,
                'head_teacher_id': classroom.head_teacher_id,
                'academic_year_id': classroom.academic_year_id,
                'student_count': classroom.student_count,
                'max_student': classroom.max_student,
                'is_active': classroom.is_active,
                'created_at': classroom.created_at.isoformat() if classroom.created_at else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi tạo lớp học',
            'error': str(e)
        }), 500

@classroom_bp.route('/api/update/<int:classroom_id>', methods=['PUT', 'POST'])
@login_required
@role_required('admin')
def update_classroom_api_v2(classroom_id):
    """
    Update classroom (API)
    PUT /classroom/api/update/<id>
    Body: {
        "class_name": "10A1",
        "grade": "10",
        "room_number": "A101",
        "head_teacher_id": 1,
        "max_student": 45,
        "is_active": true
    }
    """
    try:
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        data = request.get_json()
        
        # Validate grade if provided
        if 'grade' in data:
            if str(data['grade']) not in ALLOWED_GRADES:
                return jsonify({
                    'success': False,
                    'message': f'Invalid grade. Allowed grades: {ALLOWED_GRADES}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Check if classroom name exists in the same academic year (excluding current classroom)
        if 'class_name' in data:
            existing = ClassRoom.query.filter(
                ClassRoom.class_name == data['class_name'],
                ClassRoom.academic_year_id == classroom.academic_year_id,
                ClassRoom.id != classroom_id
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'Tên lớp "{data["class_name"]}" đã tồn tại trong niên khóa này'
                }), 400
        
        # Update fields
        if 'class_name' in data:
            classroom.class_name = data['class_name']
        if 'grade' in data:
            classroom.grade = str(data['grade'])
        if 'room_number' in data:
            classroom.room_number = data['room_number']
        if 'head_teacher_id' in data and data['head_teacher_id']:
            classroom.head_teacher_id = data['head_teacher_id']
        if 'head_teacher' in data and data['head_teacher']:
            classroom.head_teacher = data['head_teacher']
        if 'max_student' in data:
            classroom.max_student = data['max_student']
        if 'is_active' in data:
            classroom.is_active = data['is_active']
        
        classroom.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'Classroom updated: {classroom.class_name}')
        
        return jsonify({
            'success': True,
            'message': 'Cập nhật lớp học thành công',
            'data': classroom.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error updating classroom',
            'status_code': 500
        }), 500
        logger.error(f'Error updating classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi cập nhật lớp học',
            'status_code': 500
        }), 500

@classroom_bp.route('/api/<int:classroom_id>/activate', methods=['POST'])
@login_required
@role_required('admin')
def activate_classroom_api(classroom_id):
    """
    Activate classroom (API)
    POST /classroom/api/<id>/activate
    """
    try:
        from app.models.class_room import ClassRoom
        classroom = ClassRoom.query.get(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Lớp học không tồn tại'
            }), 404
        
        classroom.is_active = True
        classroom.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'Classroom activated: {classroom.class_name}')
        
        return jsonify({
            'success': True,
            'message': 'Kích hoạt lớp học thành công',
            'data': classroom.to_dict()
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error activating classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES['SYSTEM_ERROR']
        }), 500

@classroom_bp.route('/api/<int:classroom_id>/deactivate', methods=['POST'])
@login_required
@role_required('admin')
def deactivate_classroom_api(classroom_id):
    """
    Deactivate classroom (API)
    POST /classroom/api/<id>/deactivate
    """
    try:
        from app.models.class_room import ClassRoom
        classroom = ClassRoom.query.get(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Lớp học không tồn tại'
            }), 404
        
        classroom.is_active = False
        classroom.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'Classroom deactivated: {classroom.class_name}')
        
        return jsonify({
            'success': True,
            'message': 'Tạm khóa lớp học thành công',
            'data': classroom.to_dict()
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deactivating classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES['SYSTEM_ERROR']
        }), 500

@classroom_bp.route('/api/delete/<int:classroom_id>', methods=['DELETE', 'POST'])
@login_required
@role_required('admin')
def delete_classroom_api_v2(classroom_id):
    """
    Delete classroom (API)
    DELETE /classroom/api/delete/<id>
    """
    try:
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        # Check if can delete
        can_delete, message = ClassRoomService.can_delete_classroom(classroom_id)
        if not can_delete:
            return jsonify({
                'success': False,
                'message': message,
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Delete
        ClassRoomService.delete_classroom(classroom_id)
        
        logger.info(f'Classroom deleted: {classroom.class_name}')
        
        return jsonify({
            'success': True,
            'message': 'Classroom deleted',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error deleting classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to delete classroom',
            'status_code': 500
        }), 500

@classroom_bp.route('/api/students/<int:classroom_id>', methods=['GET'])
@login_required
def get_classroom_students_api_v2(classroom_id):
    """
    Get all students in classroom (API)
    GET /classroom/api/students/<id>
    Query params: page (optional), limit (optional), search (optional)
    """
    try:
        from app.models.student import Student
        
        # Check if classroom exists
        classroom = ClassRoom.query.get(classroom_id)
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Lớp học không tồn tại'
            }), 404
        
        # Get parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '').strip()
        attendance_filter = request.args.get('attendance_filter', '').strip()
        
        # Start with base query
        query = Student.query.filter_by(classroom_id=classroom_id)
        
        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Student.full_name.ilike(f'%{search}%'),
                    Student.student_id.ilike(f'%{search}%'),
                    Student.email.ilike(f'%{search}%')
                )
            )
        
        # Apply attendance filter (placeholder logic - you can implement based on actual attendance model)
        # if attendance_filter:
        #     if attendance_filter == 'present':
        #         # Add logic to filter students who are present today
        #         pass
        #     elif attendance_filter == 'absent':
        #         # Add logic to filter students who are absent today
        #         pass
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        total_pages = (total + limit - 1) // limit
        offset = (page - 1) * limit
        
        # Get students with pagination
        students = query.order_by(Student.full_name).offset(offset).limit(limit).all()
        
        students_data = []
        for student in students:
            student_dict = {
                'id': student.id,
                'full_name': student.full_name,
                'student_id': student.student_id,
                'email': student.email,
                'phone': student.phone,
                'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                'address': student.address,
                'classroom_id': student.classroom_id,
                'is_active': student.is_active,
                'last_attendance': student.created_at.isoformat() if student.created_at else None,  # Placeholder
                'attendance_today': 'unknown',  # Placeholder
                'avatar_url': None  # Placeholder
            }
            students_data.append(student_dict)
        
        return jsonify({
            'success': True,
            'message': 'Danh sách học sinh được tải thành công',
            'data': {
                'students': students_data,
                'pagination': {
                    'total': total,
                    'pages': total_pages,
                    'current_page': page,
                    'limit': limit,
                    'has_next': (page * limit) < total,
                    'has_prev': page > 1
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error retrieving classroom students: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve classroom students',
            'status_code': 500
        }), 500

@classroom_bp.route('/api/add-student', methods=['POST'])
@login_required
@role_required('admin')
def add_student_to_classroom_api():
    """
    Add student to classroom (API)
    POST /classroom/api/add-student
    Body: {
        "classroom_id": 1,
        "student_id": 1
    }
    """
    try:
        data = request.get_json()
        classroom_id = data.get('classroom_id')
        student_id = data.get('student_id')
        
        if not classroom_id or not student_id:
            return jsonify({
                'success': False,
                'message': 'Missing classroom_id or student_id',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        # Check if classroom is full
        if ClassRoomService.is_classroom_full(classroom_id):
            return jsonify({
                'success': False,
                'message': f'Classroom is full (max {MAX_STUDENTS_PER_CLASS} students)',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Add student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found',
                'status_code': 404
            }), 404
        
        student.classroom_id = classroom_id
        db.session.commit()
        
        logger.info(f'Student {student_id} added to classroom {classroom_id}')
        
        return jsonify({
            'success': True,
            'message': 'Student added to classroom',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error adding student to classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to add student to classroom',
            'status_code': 500
        }), 500

@classroom_bp.route('/api/remove-student', methods=['POST'])
@login_required
@role_required('admin')
def remove_student_from_classroom_api():
    """
    Remove student from classroom (API)
    POST /classroom/api/remove-student
    Body: {
        "classroom_id": 1,
        "student_id": 1
    }
    """
    try:
        data = request.get_json()
        classroom_id = data.get('classroom_id')
        student_id = data.get('student_id')
        
        if not classroom_id or not student_id:
            return jsonify({
                'success': False,
                'message': 'Missing classroom_id or student_id',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        # Remove student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found',
                'status_code': 404
            }), 404
        
        student.classroom_id = None
        db.session.commit()
        
        logger.info(f'Student {student_id} removed from classroom {classroom_id}')
        
        return jsonify({
            'success': True,
            'message': 'Student removed from classroom',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error removing student from classroom: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to remove student from classroom',
            'status_code': 500
        }), 500

@classroom_bp.route('/api/count/<int:classroom_id>', methods=['GET'])
@login_required
def count_classroom_students_api(classroom_id):
    """
    Get student count in classroom (API)
    GET /classroom/api/count/<id>
    """
    try:
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        
        if not classroom:
            return jsonify({
                'success': False,
                'message': 'Classroom not found',
                'status_code': 404
            }), 404
        
        count = ClassRoomService.get_classroom_student_count(classroom_id)
        
        return jsonify({
            'success': True,
            'message': 'Student count retrieved',
            'data': {
                'classroom_id': classroom_id,
                'count': count,
                'max': MAX_STUDENTS_PER_CLASS
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error counting classroom students: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to count classroom students',
            'status_code': 500
        }), 500
