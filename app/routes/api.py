"""
API Routes - Face Recognition
Các API endpoint cho nhận dạng khuôn mặt và ghi nhận điểm danh real-time
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from datetime import datetime
from app import db
from app.models.student import Student
from app.services.face_recognition_service import FaceRecognitionService
from app.services.attendance_service import AttendanceService
from app.utils.decorators import login_required, role_required
from app.utils.constants import (
    ERROR_MESSAGES, API_SUCCESS_CODE, API_BAD_REQUEST_CODE,
    MIN_FACE_CONFIDENCE, ALLOWED_IMAGE_EXTENSIONS
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ============================================================================
# HELPERS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# ============================================================================
# ROUTES
# ============================================================================

@api_bp.route('/recognize', methods=['POST'])
@login_required
def recognize_face():
    """
    Recognize face from image
    POST /api/recognize
    Body: {
        "image": "base64_encoded_image"  # OR file upload
    }
    OR Form: file (image file)
    """
    try:
        image_data = None
        
        # Try to get image from request
        if 'file' in request.files:
            # File upload
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': 'No selected file',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            
            if not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'message': f'Invalid file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            
            try:
                image = Image.open(file)
                image_data = np.array(image)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'Invalid image file',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        elif request.is_json:
            # Base64 encoded image
            data = request.get_json()
            if 'image' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Missing image data',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            
            try:
                image_base64 = data['image']
                # Remove data URL prefix if present
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                
                image_data_bytes = base64.b64decode(image_base64)
                image = Image.open(BytesIO(image_data_bytes))
                image_data = np.array(image)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'Invalid base64 image data',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        else:
            return jsonify({
                'success': False,
                'message': 'No image provided (use file upload or base64 image)',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        if image_data is None:
            return jsonify({
                'success': False,
                'message': 'Could not process image',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Recognize face using detector
        detector = FaceRecognitionService.get_detector()
        
        if not detector or not detector.model_loaded:
            return jsonify({
                'success': False,
                'message': 'Mô hình nhận diện chưa được huấn luyện',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Recognize faces in image
        recognized_faces = detector.recognize_faces_in_image(image_data, model='hog')
        
        if not recognized_faces:
            return jsonify({
                'success': True,
                'message': 'Không phát hiện khuôn mặt nào',
                'data': {
                    'recognized': False,
                    'faces': []
                },
                'status_code': API_SUCCESS_CODE
            }), API_SUCCESS_CODE
        
        # Get student information for recognized faces
        results = []
        for face_data in recognized_faces:
            face_name = face_data['name']
            confidence = face_data['confidence']
            location = face_data['location']
            
            if face_name != 'Unknown':
                # Find student by full_name
                student = Student.query.filter_by(full_name=face_name, is_active=True).first()
                
                if student:
                    results.append({
                        'student_id': student.id,
                        'student_code': student.student_code,
                        'full_name': student.full_name,
                        'classroom_id': student.classroom_id,
                        'classroom_name': student.classroom.class_name if student.classroom else None,
                        'confidence': float(round(confidence, 4)),
                        'is_confident': bool(confidence >= MIN_FACE_CONFIDENCE),
                        'location': location
                    })
                else:
                    results.append({
                        'student_id': None,
                        'full_name': face_name,
                        'confidence': float(round(confidence, 4)),
                        'is_confident': False,
                        'location': location,
                        'note': 'Student not found in database'
                    })
            else:
                results.append({
                    'student_id': None,
                    'full_name': 'Unknown',
                    'confidence': float(round(confidence, 4)),
                    'is_confident': False,
                    'location': location
                })
        
        logger.info(f'Face recognition result: {len(results)} face(s) recognized')
        
        return jsonify({
            'success': True,
            'message': 'Face recognition completed',
            'data': {
                'recognized': len(results) > 0,
                'faces': results
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error recognizing face: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Face recognition failed',
            'status_code': 500
        }), 500

@api_bp.route('/record-attendance', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def record_attendance_from_recognition():
    """
    Record attendance from face recognition result
    POST /api/record-attendance
    Body: {
        "student_id": 1,
        "classroom_id": 1,
        "session_date": "2024-01-15",
        "session_type": "morning",
        "confidence": 0.95
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'classroom_id', 'session_date', 'session_type', 'confidence']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        # Validate confidence threshold
        confidence = float(data['confidence'])
        if confidence < MIN_FACE_CONFIDENCE:
            return jsonify({
                'success': False,
                'message': f'Confidence below minimum threshold ({MIN_FACE_CONFIDENCE}). Current: {confidence}',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Record attendance
        session_date = datetime.strptime(data['session_date'], '%Y-%m-%d').date()
        
        attendance = AttendanceService.record_attendance(
            student_id=data['student_id'],
            classroom_id=data['classroom_id'],
            session_date=session_date,
            session_type=data['session_type'],
            status='present',
            confidence=confidence
        )
        
        logger.info(f'Attendance recorded from face recognition: student {data["student_id"]}')
        
        return jsonify({
            'success': True,
            'message': 'Attendance recorded successfully',
            'data': attendance.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
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

@api_bp.route('/student-readiness/<int:student_id>', methods=['GET'])
@login_required
def check_student_face_readiness(student_id):
    """
    Check if student has enough face images for recognition
    GET /api/student-readiness/<id>
    """
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found',
                'status_code': 404
            }), 404
        
        # Count face images
        from app.models.student_image import StudentImage
        image_count = StudentImage.query.filter_by(student_id=student_id).count()
        
        min_required = 3
        is_ready = image_count >= min_required
        
        # Check if model trained
        face_service = FaceRecognitionService()
        model_status = face_service.check_model_readiness()
        
        return jsonify({
            'success': True,
            'message': 'Student face readiness checked',
            'data': {
                'student_id': student_id,
                'student_name': student.name,
                'face_image_count': image_count,
                'min_required': min_required,
                'is_ready': is_ready,
                'face_recognition_status': student.face_recognition_status,
                'model_trained': model_status.get('trained', False)
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error checking student readiness: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to check student readiness',
            'status_code': 500
        }), 500

@api_bp.route('/train-model', methods=['POST'])
@login_required
@role_required('admin')
def train_face_model():
    """
    Train face recognition model
    POST /api/train-model
    """
    try:
        face_service = FaceRecognitionService()
        
        # Train model
        trained_students = face_service.train_model()
        
        logger.info(f'Face recognition model trained for {len(trained_students)} students')
        
        return jsonify({
            'success': True,
            'message': 'Model training completed',
            'data': {
                'trained_students': len(trained_students),
                'status': 'ready'
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error training model: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to train model',
            'status_code': 500
        }), 500

@api_bp.route('/model-status', methods=['GET'])
@login_required
def get_model_status():
    """
    Get face recognition model status
    GET /api/model-status
    """
    try:
        face_service = FaceRecognitionService()
        status = face_service.check_model_readiness()
        
        return jsonify({
            'success': True,
            'message': 'Model status retrieved',
            'data': status,
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error getting model status: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to get model status',
            'status_code': 500
        }), 500

@api_bp.route('/batch-recognize', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def batch_recognize_and_record():
    """
    Batch recognize and record attendance from multiple images
    POST /api/batch-recognize
    Body: {
        "classroom_id": 1,
        "session_date": "2024-01-15",
        "session_type": "morning",
        "images": [
            {
                "image": "base64_image",
                "student_id": 1
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['classroom_id', 'session_date', 'session_type', 'images']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
        
        results = []
        session_date = datetime.strptime(data['session_date'], '%Y-%m-%d').date()
        
        for img_data in data['images']:
            try:
                student_id = img_data.get('student_id')
                image_b64 = img_data.get('image')
                confidence = float(img_data.get('confidence', 1.0))
                
                if not student_id or not image_b64:
                    continue
                
                # Check confidence
                if confidence < MIN_FACE_CONFIDENCE:
                    results.append({
                        'student_id': student_id,
                        'recorded': False,
                        'reason': f'Confidence below threshold ({confidence} < {MIN_FACE_CONFIDENCE})'
                    })
                    continue
                
                # Record attendance
                attendance = AttendanceService.record_attendance(
                    student_id=student_id,
                    classroom_id=data['classroom_id'],
                    session_date=session_date,
                    session_type=data['session_type'],
                    status='present',
                    confidence=confidence
                )
                
                results.append({
                    'student_id': student_id,
                    'recorded': True,
                    'attendance_id': attendance.id
                })
                
            except Exception as e:
                logger.warning(f'Error recording attendance for image: {str(e)}')
                results.append({
                    'student_id': img_data.get('student_id'),
                    'recorded': False,
                    'reason': str(e)
                })
        
        logger.info(f'Batch attendance recorded: {len([r for r in results if r["recorded"]])} records')
        
        return jsonify({
            'success': True,
            'message': 'Batch attendance recording completed',
            'data': {
                'total_processed': len(results),
                'successful': len([r for r in results if r['recorded']]),
                'failed': len([r for r in results if not r['recorded']]),
                'details': results
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
        logger.error(f'Error in batch recognize: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Batch processing failed',
            'status_code': 500
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint (no auth required)
    GET /api/health
    """
    try:
        return jsonify({
            'success': True,
            'message': 'API is healthy',
            'status': 'running',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'API health check failed',
            'status_code': 500
        }), 500


# ============================================================================
# ADMIN STATS API ENDPOINTS
# ============================================================================

@api_bp.route('/admin/stats', methods=['GET'])
@login_required
@role_required('admin')
def get_admin_stats():
    """
    Get admin statistics
    GET /api/admin/stats
    """
    try:
        from app.models.user import User
        from app.models.student import Student
        from app.models.class_room import ClassRoom
        from app.models.attendance import Attendance
        
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_teachers = User.query.filter_by(role='teacher').count()
        total_admins = User.query.filter_by(role='admin').count()
        total_students = Student.query.count()
        total_classrooms = ClassRoom.query.count()
        total_attendance_records = Attendance.query.count()
        
        return jsonify({
            'success': True,
            'message': 'Statistics retrieved',
            'data': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'teachers': total_teachers,
                    'admins': total_admins
                },
                'students': total_students,
                'classrooms': total_classrooms,
                'attendance_records': total_attendance_records
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving admin statistics: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve statistics',
            'status_code': 500
        }), 500
