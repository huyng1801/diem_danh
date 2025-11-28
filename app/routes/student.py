"""
Student Routes
Các endpoint quản lý học sinh và ảnh khuôn mặt
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app import db
from app.models.student import Student
from app.models.student_image import StudentImage
from app.models.class_room import ClassRoom
from app.models.academic_year import AcademicYear
from app.utils.decorators import login_required, role_required
from app.utils.validators import is_valid_phone
from app.utils.helpers import ensure_upload_directories
import logging

logger = logging.getLogger(__name__)

# Create blueprint
student_bp = Blueprint('student', __name__, url_prefix='/student')

# Constants
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE_MB = 5
API_SUCCESS_CODE = 200
API_CREATED_CODE = 201
API_BAD_REQUEST_CODE = 400

# ============================================================================
# HELPERS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def is_valid_image_file(filepath):
    """Validate if file is a real image"""
    try:
        from PIL import Image
        img = Image.open(filepath)
        img.verify()
        return True
    except Exception:
        return False

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return 0
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

# ============================================================================
# PAGE ROUTES (Render Templates)
# ============================================================================

@student_bp.route('/list', methods=['GET'])
@login_required
def list():
    """Student list page"""
    try:
        return render_template('student/list.html')
    except Exception as e:
        logger.error(f'Error rendering student list page: {str(e)}')
        return redirect(url_for('admin.dashboard'))

@student_bp.route('/form', methods=['GET'])
@login_required
@role_required('admin', 'teacher')
def form():
    """Student form page (create/edit)"""
    try:
        student_id = request.args.get('id', type=int)
        student_data = None
        
        if student_id:
            student_data = Student.query.get(student_id)
            if not student_data:
                return redirect(url_for('student.list'))
        
        return render_template('student/form.html', student_data=student_data)
    except Exception as e:
        logger.error(f'Error rendering student form page: {str(e)}')
        return redirect(url_for('student.list'))

@student_bp.route('/<int:student_id>/detail', methods=['GET'])
@login_required
def detail(student_id):
    """Student detail page"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return redirect(url_for('student.list'))
        
        # Calculate age
        student_age = calculate_age(student.date_of_birth) if student.date_of_birth else None
        
        # Get face images count
        face_images_count = StudentImage.query.filter_by(student_id=student_id).count()
        
        # Get attendance statistics
        from app.models.attendance import Attendance
        attendance_logs = Attendance.query.filter_by(student_id=student_id).all()
        
        present_count = sum(1 for log in attendance_logs if log.status == 'present')
        absent_count = sum(1 for log in attendance_logs if log.status == 'absent')
        late_count = sum(1 for log in attendance_logs if log.status == 'late')
        total_count = len(attendance_logs)
        
        attendance_rate = (present_count / total_count * 100) if total_count > 0 else 0
        
        attendance_stats = {
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'total_count': total_count,
            'attendance_rate': attendance_rate
        }
        
        # Get recent activities (simplified version)
        recent_activities = []
        
        return render_template(
            'student/detail.html',
            student=student,
            student_age=student_age,
            face_images_count=face_images_count,
            attendance_stats=attendance_stats,
            recent_activities=recent_activities
        )
    except Exception as e:
        logger.error(f'Error rendering student detail page: {str(e)}')
        return redirect(url_for('student.list'))

@student_bp.route('/<int:student_id>/image-upload', methods=['GET'])
@login_required
@role_required('admin', 'teacher')
def image_upload(student_id):
    """Student image upload page"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return redirect(url_for('student.list'))
        
        # Get face images count
        face_images_count = StudentImage.query.filter_by(student_id=student_id).count()
        
        return render_template(
            'student/image_upload.html',
            student=student,
            face_images_count=face_images_count
        )
    except Exception as e:
        logger.error(f'Error rendering image upload page: {str(e)}')
        return redirect(url_for('student.list'))

@student_bp.route('/<int:student_id>/image-gallery', methods=['GET'])
@login_required
def image_gallery(student_id):
    """Student image gallery page"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return redirect(url_for('student.list'))
        
        # Get all face images
        face_images = StudentImage.query.filter_by(student_id=student_id).order_by(
            StudentImage.created_at.desc()
        ).all()
        
        return render_template(
            'student/image_gallery.html',
            student=student,
            face_images=face_images
        )
    except Exception as e:
        logger.error(f'Error rendering image gallery page: {str(e)}')
        return redirect(url_for('student.list'))

# ============================================================================
# API ROUTES
# ============================================================================

@student_bp.route('/api/list', methods=['GET'])
@login_required
def api_list_students():
    """Get all students with filters"""
    try:
        classroom_id = request.args.get('classroom_id', type=int)
        gender = request.args.get('gender', type=str)
        is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true' if x else None)
        search = request.args.get('search', type=str)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Base query
        query = Student.query
        
        # Apply filters
        if classroom_id:
            query = query.filter_by(classroom_id=classroom_id)
        
        if gender:
            query = query.filter_by(gender=gender)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        if search:
            query = query.filter(
                db.or_(
                    Student.full_name.ilike(f'%{search}%'),
                    Student.student_code.ilike(f'%{search}%')
                )
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Get all students and sort by grade and name
        all_students = query.all()
        
        # Import service to use name parsing
        from app.services.student_service import StudentService
        sorted_students = sorted(all_students, key=lambda s: (
            s.classroom.grade if s.classroom else '',
            StudentService._parse_vietnamese_name(s.full_name)
        ))
        
        # Apply pagination on sorted list
        students = sorted_students[(page - 1) * limit:(page - 1) * limit + limit]
        
        # Build response with face recognition status
        students_data = []
        for student in students:
            student_dict = student.to_dict()
            
            # Get face images count
            face_images_count = StudentImage.query.filter_by(student_id=student.id).count()
            student_dict['face_images_count'] = face_images_count
            student_dict['face_recognition_enabled'] = face_images_count >= 3
            
            # Add classroom information
            if student.classroom:
                student_dict['classroom'] = {
                    'id': student.classroom.id,
                    'class_name': student.classroom.class_name,
                    'grade': student.classroom.grade
                }
            else:
                student_dict['classroom'] = None
            
            students_data.append(student_dict)
        
        return jsonify({
            'success': True,
            'message': 'Students retrieved',
            'data': {
                'students': students_data,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving students: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve students',
            'status_code': 500
        }), 500

@student_bp.route('/api/create', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_create_student():
    """Create new student"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_code', 'full_name', 'gender', 'date_of_birth']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Trường {field} là bắt buộc',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Check if student code already exists
        existing_student = Student.query.filter_by(student_code=data['student_code']).first()
        if existing_student:
            return jsonify({
                'success': False,
                'message': 'Mã học sinh đã tồn tại',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Validate phone if provided
        if data.get('phone') and not is_valid_phone(data['phone']):
            return jsonify({
                'success': False,
                'message': 'Số điện thoại không hợp lệ',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Validate parent phone if provided
        if data.get('parent_phone') and not is_valid_phone(data['parent_phone']):
            return jsonify({
                'success': False,
                'message': 'Số điện thoại phụ huynh không hợp lệ',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Create student
        student = Student(
            student_code=data['student_code'],
            full_name=data['full_name'],
            gender=data['gender'],
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date(),
            phone=data.get('phone'),
            address=data.get('address'),
            parent_name=data.get('parent_name'),
            parent_phone=data.get('parent_phone'),
            classroom_id=data.get('classroom_id'),
            academic_year_id=data.get('academic_year_id'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(student)
        db.session.commit()
        
        logger.info(f'Student created: {student.full_name}')
        
        return jsonify({
            'success': True,
            'message': 'Tạo học sinh thành công',
            'data': student.to_dict(),
            'status_code': API_CREATED_CODE
        }), API_CREATED_CODE
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating student: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi tạo học sinh',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>', methods=['GET'])
@login_required
def api_get_student(student_id):
    """Get student by ID"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        student_data = student.to_dict()
        
        # Get face images count
        face_images_count = StudentImage.query.filter_by(student_id=student_id).count()
        student_data['face_images_count'] = face_images_count
        student_data['face_recognition_enabled'] = face_images_count >= 3
        
        return jsonify({
            'success': True,
            'message': 'Học sinh được tải thành công',
            'data': student_data,
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving student: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi tải học sinh',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>', methods=['PUT'])
@login_required
@role_required('admin', 'teacher')
def api_update_student(student_id):
    """Update student"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        data = request.get_json()
        
        # Validate phone if provided
        if data.get('phone') and not is_valid_phone(data['phone']):
            return jsonify({
                'success': False,
                'message': 'Số điện thoại không hợp lệ',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Validate parent phone if provided
        if data.get('parent_phone') and not is_valid_phone(data['parent_phone']):
            return jsonify({
                'success': False,
                'message': 'Số điện thoại phụ huynh không hợp lệ',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Update fields
        if 'full_name' in data:
            student.full_name = data['full_name']
        if 'gender' in data:
            student.gender = data['gender']
        if 'date_of_birth' in data:
            student.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        if 'phone' in data:
            student.phone = data['phone']
        if 'address' in data:
            student.address = data['address']
        if 'parent_name' in data:
            student.parent_name = data['parent_name']
        if 'parent_phone' in data:
            student.parent_phone = data['parent_phone']
        if 'classroom_id' in data:
            student.classroom_id = data['classroom_id']
        if 'academic_year_id' in data:
            student.academic_year_id = data['academic_year_id']
        if 'is_active' in data:
            student.is_active = data['is_active']
        
        db.session.commit()
        
        logger.info(f'Student updated: {student.full_name}')
        
        return jsonify({
            'success': True,
            'message': 'Cập nhật học sinh thành công',
            'data': student.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating student: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi cập nhật học sinh',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def api_delete_student(student_id):
    """Delete student"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        # Delete student images
        images = StudentImage.query.filter_by(student_id=student_id).all()
        for image in images:
            try:
                if os.path.exists(image.file_path):
                    os.remove(image.file_path)
            except Exception as e:
                logger.warning(f'Could not delete image file: {str(e)}')
            db.session.delete(image)
        
        # Delete student
        db.session.delete(student)
        db.session.commit()
        
        logger.info(f'Student deleted: {student.full_name}')
        
        return jsonify({
            'success': True,
            'message': 'Xóa học sinh thành công',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting student: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi xóa học sinh',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>/activate', methods=['PUT', 'POST'])
@login_required
@role_required('admin', 'teacher')
def api_activate_student(student_id):
    """Activate student account"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        student.is_active = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kích hoạt tài khoản học sinh thành công',
            'data': student.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error activating student: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi kích hoạt tài khoản',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>/deactivate', methods=['PUT', 'POST'])
@login_required
@role_required('admin', 'teacher')
def api_deactivate_student(student_id):
    """Deactivate student account"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        student.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Khóa tài khoản học sinh thành công',
            'data': student.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deactivating student: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi khóa tài khoản',
            'status_code': 500
        }), 500

@student_bp.route('/api/generate-code', methods=['GET'])
@login_required
def api_generate_student_code():
    """Generate unique student code"""
    try:
        # Get current year
        current_year = datetime.now().year
        
        # Get highest student code for current year
        latest_student = Student.query.filter(
            Student.student_code.like(f'HS{current_year}%')
        ).order_by(Student.student_code.desc()).first()
        
        if latest_student:
            # Extract number from code and increment
            try:
                code_number = int(latest_student.student_code[6:]) + 1
            except:
                code_number = 1
        else:
            code_number = 1
        
        # Generate new code
        student_code = f'HS{current_year}{code_number:05d}'
        
        return jsonify({
            'success': True,
            'message': 'Student code generated',
            'data': {
                'student_code': student_code
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error generating student code: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi tạo mã học sinh',
            'status_code': 500
        }), 500

# ============================================================================
# IMAGE UPLOAD & MANAGEMENT API ROUTES
# ============================================================================

@student_bp.route('/api/<int:student_id>/upload-image', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_upload_image(student_id):
    """Upload student face image"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy file ảnh',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        file = request.files['image']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Vui lòng chọn file ảnh',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': f'Định dạng file không hợp lệ. Chỉ chấp nhận: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size_bytes = file.tell()
        file_size_mb = file_size_bytes / (1024 * 1024)
        file.seek(0)
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            return jsonify({
                'success': False,
                'message': f'File quá lớn (tối đa {MAX_FILE_SIZE_MB}MB)',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Ensure upload directory exists
        ensure_upload_directories()
        
        try:
            # Use student_code for folder name (more reliable than full_name)
            upload_dir = os.path.join('app', 'uploads', 'student_faces', student.student_code)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate safe filename with timestamp
            file_ext = os.path.splitext(file.filename)[1].lower()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # milliseconds
            safe_filename = f'{student.student_code}_{timestamp}{file_ext}'
            filepath = os.path.join(upload_dir, safe_filename)
            
            # Save file
            file.save(filepath)
            logger.info(f'File saved to: {filepath}')
            
            # Validate image file
            if not is_valid_image_file(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
                return jsonify({
                    'success': False,
                    'message': 'File không phải là ảnh hợp lệ hoặc bị hỏng',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            
            # Create relative URL for serving
            image_url = f'/uploads/student_faces/{student.student_code}/{safe_filename}'
            
            # Create database record
            image = StudentImage(
                student_id=student_id,
                image_url=image_url,
                image_path=filepath,
                file_size=file_size_bytes,
                is_valid=True
            )
            
            db.session.add(image)
            db.session.commit()
            
            # Update student's face recognition status
            student.update_face_recognition_status()
            db.session.commit()
            
            logger.info(f'Image uploaded successfully for student {student_id}: {safe_filename}')
            
            # Return image data with proper URL
            image_data = image.to_dict()
            image_data['image_path'] = image_url  # Use URL for frontend display
            image_data['filename'] = safe_filename
            
            return jsonify({
                'success': True,
                'message': 'Tải lên ảnh thành công',
                'data': image_data,
                'status_code': API_CREATED_CODE
            }), API_CREATED_CODE
            
        except Exception as e:
            logger.error(f'Error saving image: {str(e)}')
            # Try to clean up file if database insert failed
            try:
                if 'filepath' in locals() and os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass
            return jsonify({
                'success': False,
                'message': f'Lỗi khi lưu ảnh: {str(e)}',
                'status_code': 500
            }), 500
        
    except Exception as e:
        logger.error(f'Error uploading image: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải lên ảnh: {str(e)}',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>/images', methods=['GET'])
@login_required
def api_get_images(student_id):
    """Get all images for student"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Query images with is_valid=True by default
        images_query = StudentImage.query.filter_by(
            student_id=student_id,
            is_valid=True
        ).order_by(StudentImage.created_at.desc())
        
        total_images = images_query.count()
        
        # Pagination
        start = (page - 1) * limit
        images = images_query.offset(start).limit(limit).all()
        
        # Prepare image data with proper URLs
        images_data = []
        for img in images:
            img_dict = img.to_dict()
            # Ensure image_path is the URL (not filesystem path)
            if img.image_url:
                img_dict['image_path'] = img.image_url
            else:
                # Fallback: construct URL from image_path if image_url is missing
                if img.image_path:
                    # Extract relative path from full path
                    uploads_index = img.image_path.find('uploads')
                    if uploads_index != -1:
                        relative_path = img.image_path[uploads_index:]
                        img_dict['image_path'] = '/' + relative_path.replace('\\', '/')
                    else:
                        img_dict['image_path'] = img.image_url or ''
            
            # Add filename for display
            img_dict['filename'] = os.path.basename(img.image_path) if img.image_path else 'unknown.jpg'
            
            # Add quality assessment (placeholder - can be enhanced with actual quality detection)
            img_dict['quality'] = 'good' if img.quality_score and img.quality_score > 0.7 else 'medium'
            
            images_data.append(img_dict)
        
        logger.info(f'Retrieved {len(images_data)} images for student {student_id}')
        
        return jsonify({
            'success': True,
            'message': 'Ảnh học sinh được tải thành công',
            'data': {
                'images': images_data,
                'count': total_images,
                'total': total_images,
                'page': page,
                'limit': limit,
                'pages': (total_images + limit - 1) // limit if total_images > 0 else 0
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving student images: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải ảnh học sinh: {str(e)}',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>/delete-image/<int:image_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'teacher')
def api_delete_image(student_id, image_id):
    """Delete student image"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        image = StudentImage.query.filter_by(id=image_id, student_id=student_id).first()
        
        if not image:
            return jsonify({
                'success': False,
                'message': 'Ảnh không tìm thấy',
                'status_code': 404
            }), 404
        
        # Delete file from disk - try both image_path and image_url
        try:
            file_path = None
            if image.image_path and os.path.exists(image.image_path):
                file_path = image.image_path
            elif image.image_url:
                # Convert URL to file path
                url_path = image.image_url.replace('/uploads/', 'app/uploads/').lstrip('/')
                if os.path.exists(url_path):
                    file_path = url_path
            
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f'Deleted image file: {file_path}')
        except Exception as e:
            logger.warning(f'Could not delete image file: {str(e)}')
        
        # Delete from database
        db.session.delete(image)
        db.session.commit()
        
        # Update student's face recognition status
        student.update_face_recognition_status()
        db.session.commit()
        
        logger.info(f'Image deleted for student {student_id}')
        
        return jsonify({
            'success': True,
            'message': 'Xóa ảnh thành công',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting image: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi xóa ảnh',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>/delete-images', methods=['DELETE'])
@login_required
@role_required('admin', 'teacher')
def api_delete_images(student_id):
    """Delete multiple student images"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({
                'success': False,
                'message': 'Không có ảnh được chọn',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Delete all specified images
        images = StudentImage.query.filter(
            StudentImage.id.in_(image_ids),
            StudentImage.student_id == student_id
        ).all()
        
        deleted_count = 0
        for image in images:
            # Delete file from disk - try both image_path and image_url
            try:
                file_path = None
                if image.image_path and os.path.exists(image.image_path):
                    file_path = image.image_path
                elif image.image_url:
                    # Convert URL to file path
                    url_path = image.image_url.replace('/uploads/', 'app/uploads/').lstrip('/')
                    if os.path.exists(url_path):
                        file_path = url_path
                
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f'Deleted image file: {file_path}')
            except Exception as e:
                logger.warning(f'Could not delete image file: {str(e)}')
            
            db.session.delete(image)
            deleted_count += 1
        
        db.session.commit()
        
        # Update student's face recognition status
        student.update_face_recognition_status()
        db.session.commit()
        
        logger.info(f'Deleted {deleted_count} images for student {student_id}')
        
        return jsonify({
            'success': True,
            'message': f'Xóa {deleted_count} ảnh thành công',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting images: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi xóa ảnh',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>/retrain', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_retrain_model(student_id):
    """Retrain face recognition model for student"""
    try:
        from app.services.face_recognition_service import FaceRecognitionService
        
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        # Get student images
        images = StudentImage.query.filter_by(student_id=student_id, is_valid=True).all()
        
        if len(images) < 3:
            return jsonify({
                'success': False,
                'message': 'Cần ít nhất 3 ảnh để huấn luyện mô hình',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Train model for all students
        results = FaceRecognitionService.train_model()
        
        if results['success']:
            logger.info(f'Model retrained successfully. Trained {results["trained_count"]} students')
            return jsonify({
                'success': True,
                'message': f'Huấn luyện mô hình thành công. Đã huấn luyện {results["trained_count"]} học sinh.',
                'data': {
                    'trained_count': results['trained_count'],
                    'total_encodings': results.get('total_encodings', 0)
                },
                'status_code': API_SUCCESS_CODE
            }), API_SUCCESS_CODE
        else:
            return jsonify({
                'success': False,
                'message': results.get('message', 'Lỗi khi huấn luyện mô hình'),
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
    except Exception as e:
        logger.error(f'Error retraining model: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi huấn luyện mô hình',
            'status_code': 500
        }), 500

@student_bp.route('/api/<int:student_id>/set-thumbnail', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_set_thumbnail(student_id):
    """Set student thumbnail image"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Học sinh không tìm thấy',
                'status_code': 404
            }), 404
        
        data = request.get_json()
        image_id = data.get('image_id')
        
        if not image_id:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy ID ảnh',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        image = StudentImage.query.filter_by(id=image_id, student_id=student_id).first()
        
        if not image:
            return jsonify({
                'success': False,
                'message': 'Ảnh không tìm thấy',
                'status_code': 404
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Đặt ảnh đại diện thành công',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error setting thumbnail: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi khi đặt ảnh đại diện',
            'status_code': 500
        }), 500
