from app import db
from app.models.student import Student
from app.models.student_image import StudentImage
from app.models.class_room import ClassRoom
from ml_models import FaceTrainer, FaceDetector
from app.utils.constants import (
    MIN_FACE_CONFIDENCE, DEFAULT_FACE_CONFIDENCE, 
    MIN_FACE_IMAGES, ERROR_MESSAGES
)
from app.utils.helpers import get_student_faces_path, ensure_upload_directories
import os
import logging

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    
    _detector = None
    _model_trained = False
    
    @staticmethod
    def init_detector(confidence_threshold=DEFAULT_FACE_CONFIDENCE):
        try:
            FaceRecognitionService._detector = FaceDetector(confidence_threshold=confidence_threshold)
            if FaceRecognitionService._detector.load_model():
                FaceRecognitionService._model_trained = True
                logger.info('Face detection model loaded successfully')
                return True
            logger.warning('Face detection model not found or failed to load')
            return False
        except Exception as e:
            logger.error(f'Error initializing face detector: {str(e)}')
            return False
    
    @staticmethod
    def get_detector():
        if FaceRecognitionService._detector is None:
            FaceRecognitionService.init_detector()
        return FaceRecognitionService._detector
    
    @staticmethod
    def is_model_trained():
        return FaceRecognitionService._model_trained
    
    @staticmethod
    def check_model_readiness():
        """Check if face recognition model is ready to use"""
        try:
            from ml_models.face_trainer import FaceTrainer
            import os
            
            trainer = FaceTrainer()
            model_file = os.path.join(trainer.trained_models_dir, 'face_recognition_model.pkl')
            model_exists = os.path.exists(model_file)
            
            # Try to load model if exists
            detector = FaceRecognitionService.get_detector()
            model_loaded = detector is not None and FaceRecognitionService.is_model_trained()
            
            # Count trained students
            trained_count = 0
            if model_loaded and detector.known_face_encodings:
                trained_count = len(detector.known_face_encodings)
            
            return {
                'model_exists': model_exists,
                'model_loaded': model_loaded,
                'trained': FaceRecognitionService._model_trained,
                'trained_count': trained_count,
                'ready': model_loaded and trained_count > 0
            }
        except Exception as e:
            logger.error(f'Error checking model readiness: {str(e)}')
            return {
                'model_exists': False,
                'model_loaded': False,
                'trained': False,
                'trained_count': 0,
                'ready': False,
                'error': str(e)
            }
    
    @staticmethod
    def train_model():
        """Train face recognition model using student database"""
        from ml_models.face_trainer import FaceTrainer
        import os
        
        trainer = FaceTrainer()
        student_faces_dir = trainer.student_faces_dir
        
        # Get all active students with enough face images
        students = db.session.query(Student).filter_by(
            is_active=True
        ).filter(
            Student.face_images_count >= 3
        ).all()
        
        if not students:
            logger.warning('No students ready for training')
            return {
                'success': False,
                'message': 'Không có học sinh nào sẵn sàng để huấn luyện (cần ít nhất 3 ảnh)',
                'trained_count': 0,
                'failed_count': 0,
                'trained_persons': [],
                'failed_persons': []
            }
        
        # Filter students that actually have folder with images
        students_with_folders = []
        for student in students:
            folder_path = os.path.join(student_faces_dir, student.student_code)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Check if folder has images
                image_files = [f for f in os.listdir(folder_path) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]
                if len(image_files) >= 2:  # At least 2 images
                    students_with_folders.append(student)
                else:
                    logger.warning(f'Student {student.student_code} has folder but only {len(image_files)} images')
            else:
                logger.warning(f'Student {student.student_code} has no folder at {folder_path}')
        
        if not students_with_folders:
            logger.warning(f'No students with actual image folders found (checked {len(students)} students)')
            return {
                'success': False,
                'message': f'Không tìm thấy folder ảnh cho {len(students)} học sinh. Vui lòng kiểm tra lại.',
                'trained_count': 0,
                'failed_count': len(students),
                'trained_persons': [],
                'failed_persons': []
            }
        
        logger.info(f'Starting training for {len(students_with_folders)} students (filtered from {len(students)})')
        
        known_encodings = []
        known_names = []
        trained_persons = []
        failed_persons = []
        
        for idx, student in enumerate(students_with_folders):
            logger.info(f'[{idx + 1}/{len(students_with_folders)}] Training {student.student_code} - {student.full_name}')
            
            try:
                # Train using student_code as folder name
                success, message, encodings = trainer.train_person(
                    person_name=student.student_code,  # Folder name is student_code
                    model='hog',
                    min_images=2
                )
                
                if success and encodings:
                    # Store encodings with full_name for recognition
                    for encoding in encodings:
                        known_encodings.append(encoding)
                        known_names.append(student.full_name)  # Use full_name for recognition
                    
                    trained_persons.append({
                        'student_code': student.student_code,
                        'full_name': student.full_name,
                        'encodings_count': len(encodings),
                        'message': message
                    })
                    logger.info(f'✓ Successfully trained {student.full_name} with {len(encodings)} encodings')
                else:
                    failed_persons.append({
                        'student_code': student.student_code,
                        'full_name': student.full_name,
                        'message': message
                    })
                    logger.warning(f'✗ Failed to train {student.full_name}: {message}')
            except Exception as e:
                logger.error(f'Exception training {student.student_code}: {str(e)}')
                failed_persons.append({
                    'student_code': student.student_code,
                    'full_name': student.full_name,
                    'message': f'Lỗi: {str(e)}'
                })
        
        # Save model if we have encodings
        results = {
            'success': len(trained_persons) > 0,
            'trained_count': len(trained_persons),
            'failed_count': len(failed_persons),
            'total_encodings': len(known_encodings),
            'trained_persons': trained_persons,
            'failed_persons': failed_persons,
            'message': f'Đã huấn luyện {len(trained_persons)}/{len(students_with_folders)} học sinh'
        }
        
        if known_encodings:
            model_path = trainer.save_model(known_encodings, known_names)
            results['model_path'] = model_path
            
            # Reload detector model
            FaceRecognitionService._model_trained = True
            if FaceRecognitionService._detector:
                FaceRecognitionService._detector.load_model()
            
            logger.info(f'Training completed: {len(trained_persons)} students trained, {len(known_encodings)} total encodings')
        else:
            logger.error('No encodings generated during training')
            results['message'] = 'Không thể tạo encodings cho bất kỳ học sinh nào'
        
        return results
    
    @staticmethod
    def add_student_face(student_id, image_path, uploaded_by_id=None):
        student = db.session.query(Student).get(student_id)
        if not student:
            raise ValueError("Student not found")
        
        if not os.path.exists(image_path):
            raise ValueError("Image file not found")
        
        file_size = os.path.getsize(image_path)
        if file_size > 5 * 1024 * 1024:
            raise ValueError("Image size exceeds 5MB limit")
        
        image_url = f"/uploads/student_faces/{student.student_code}/{os.path.basename(image_path)}"
        
        image = StudentImage(
            student_id=student_id,
            image_url=image_url,
            image_path=image_path,
            file_size=file_size,
            is_valid=True,
            uploaded_by_id=uploaded_by_id
        )
        db.session.add(image)
        db.session.commit()
        
        student.update_face_recognition_status()
        db.session.commit()
        
        return image
    
    @staticmethod
    def recognize_student_face(image_rgb, classroom_id=None):
        detector = FaceRecognitionService.get_detector()
        
        if not detector.model_loaded:
            return None, "Model not loaded"
        
        faces = detector.recognize_faces_in_image(image_rgb, model='hog')
        
        if not faces:
            return None, "No face detected"
        
        best_face = max(faces, key=lambda f: f['confidence'])
        
        if best_face['confidence'] < MIN_FACE_CONFIDENCE:
            return None, f"Confidence too low: {best_face['confidence']:.2%}"
        
        if best_face['name'] == "Unknown":
            return None, "Face not recognized"
        
        student = db.session.query(Student).filter_by(
            full_name=best_face['name'],
            is_active=True
        ).first()
        
        if classroom_id and student and student.classroom_id != classroom_id:
            return None, "Student not in this class"
        
        return {
            'student': student,
            'confidence': best_face['confidence'],
            'location': best_face['location']
        }, None
    
    @staticmethod
    def get_classroom_recognizable_students(classroom_id):
        return db.session.query(Student).filter_by(
            classroom_id=classroom_id,
            is_active=True,
            face_recognition_enabled=True
        ).all()
    
    @staticmethod
    def get_student_face_images(student_id):
        return db.session.query(StudentImage).filter_by(
            student_id=student_id,
            is_valid=True
        ).all()
    
    @staticmethod
    def check_student_face_readiness(student_id):
        student = db.session.query(Student).get(student_id)
        if not student:
            raise ValueError("Student not found")
        
        image_count = db.session.query(StudentImage).filter_by(
            student_id=student_id,
            is_valid=True
        ).count()
        
        return {
            'student_id': student_id,
            'student_code': student.student_code,
            'full_name': student.full_name,
            'image_count': image_count,
            'is_ready': image_count >= 3,
            'is_enabled': student.face_recognition_enabled
        }
    
    @staticmethod
    def retrain_if_needed():
        students_ready = db.session.query(Student).filter_by(
            face_recognition_enabled=True
        ).count()
        
        if students_ready > 0:
            try:
                FaceRecognitionService.train_model()
                logger.info(f"Model retrained. Ready for {students_ready} students")
                return True
            except Exception as e:
                logger.error(f"Model retraining failed: {str(e)}")
                return False
        
        return False
