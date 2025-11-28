from app import db
from app.models.student import Student
from app.models.student_image import StudentImage
from app.models.class_room import ClassRoom
from app.utils.validators import (
    is_valid_image_file, is_valid_phone, validate_student_data
)
from app.utils.helpers import (
    get_student_faces_path, ensure_upload_directories, 
    delete_file, delete_directory
)
from app.utils.constants import (
    MIN_FACE_IMAGES, MAX_FACE_IMAGES_PER_STUDENT, ERROR_MESSAGES,
    ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE
)
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class StudentService:
    
    @staticmethod
    def _parse_vietnamese_name(full_name):
        """
        Phân tách tên tiếng Việt: Họ Tên đệm Tên
        Trả về tuple: (first_name, middle_name, last_name)
        Quy tắc: Phần cuối cùng là tên, phần đầu tiên là họ, phần giữa là tên đệm
        """
        if not full_name:
            return ('', '', '')
        
        parts = full_name.strip().split()
        if len(parts) == 1:
            return ('', '', parts[0])  # Chỉ có tên
        elif len(parts) == 2:
            return ('', parts[0], parts[1])  # Họ và tên
        else:
            # Họ + tên đệm + tên
            return (parts[-1], ' '.join(parts[1:-1]), parts[0])
    
    @staticmethod
    def create_student(student_code, full_name, gender, date_of_birth, 
                      classroom_id=None, address=None, phone=None, 
                      parent_name=None, parent_phone=None):
        try:
            # Validate input data
            if db.session.query(Student).filter_by(student_code=student_code).first():
                raise ValueError(ERROR_MESSAGES['DUPLICATE_STUDENT_CODE'])
            
            if classroom_id and not db.session.query(ClassRoom).get(classroom_id):
                raise ValueError(ERROR_MESSAGES['CLASSROOM_NOT_FOUND'])
            
            # Validate phone numbers if provided
            if phone and not is_valid_phone(phone):
                raise ValueError(ERROR_MESSAGES['INVALID_PHONE'])
            
            if parent_phone and not is_valid_phone(parent_phone):
                raise ValueError(ERROR_MESSAGES['INVALID_PHONE'])
            
            student = Student(
                student_code=student_code,
                full_name=full_name,
                gender=gender,
                date_of_birth=date_of_birth,
                classroom_id=classroom_id,
                address=address,
                phone=phone,
                parent_name=parent_name,
                parent_phone=parent_phone
            )
            db.session.add(student)
            db.session.commit()
            
            # Create face images directory
            ensure_upload_directories()
            get_student_faces_path(student_code)
            
            logger.info(f'Student created successfully: {student_code}')
            return student
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error creating student {student_code}: {str(e)}')
            raise
    
    @staticmethod
    def get_student_by_id(student_id):
        return db.session.query(Student).filter_by(id=student_id).first()
    
    @staticmethod
    def get_student_by_code(student_code):
        return db.session.query(Student).filter_by(student_code=student_code).first()
    
    @staticmethod
    def get_students_by_classroom(classroom_id):
        students = db.session.query(Student).filter_by(
            classroom_id=classroom_id,
            is_active=True
        ).all()
        # Sắp xếp theo tên (tên, tên đệm, họ)
        return sorted(students, key=lambda s: StudentService._parse_vietnamese_name(s.full_name))
    
    @staticmethod
    def get_all_active_students():
        students = db.session.query(Student).filter_by(is_active=True).all()
        # Sắp xếp theo tên (tên, tên đệm, họ)
        return sorted(students, key=lambda s: StudentService._parse_vietnamese_name(s.full_name))
    
    @staticmethod
    def search_students(query):
        return db.session.query(Student).filter(
            db.or_(
                Student.full_name.ilike(f'%{query}%'),
                Student.student_code.ilike(f'%{query}%')
            )
        ).filter_by(is_active=True).order_by(Student.full_name).all()
    
    @staticmethod
    def update_student(student_id, **kwargs):
        student = StudentService.get_student_by_id(student_id)
        if not student:
            raise ValueError("Student not found")
        
        allowed_fields = ['full_name', 'gender', 'date_of_birth', 'address', 
                         'phone', 'parent_name', 'parent_phone', 'avatar_url']
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(student, key, value)
        
        student.updated_at = datetime.utcnow()
        db.session.commit()
        return student
    
    @staticmethod
    def assign_to_classroom(student_id, classroom_id):
        student = StudentService.get_student_by_id(student_id)
        if not student:
            raise ValueError("Student not found")
        
        classroom = db.session.query(ClassRoom).get(classroom_id)
        if not classroom:
            raise ValueError("Classroom not found")
        
        if classroom.is_full() and student.classroom_id != classroom_id:
            raise ValueError("Classroom is full")
        
        old_classroom_id = student.classroom_id
        student.classroom_id = classroom_id
        db.session.commit()
        return student
    
    @staticmethod
    def get_student_images(student_id):
        return db.session.query(StudentImage).filter_by(
            student_id=student_id,
            is_valid=True
        ).all()
    
    @staticmethod
    def add_student_image(student_id, image_file, angle=None, 
                         quality_score=0.0, uploaded_by_id=None):
        try:
            student = StudentService.get_student_by_id(student_id)
            if not student:
                raise ValueError(ERROR_MESSAGES['STUDENT_NOT_FOUND'])
            
            # Check if student already has max images
            current_images = db.session.query(StudentImage).filter_by(
                student_id=student_id, is_valid=True
            ).count()
            
            if current_images >= MAX_FACE_IMAGES_PER_STUDENT:
                raise ValueError(f"Student already has maximum {MAX_FACE_IMAGES_PER_STUDENT} face images")
            
            # Validate image file
            if not is_valid_image_file(image_file):
                raise ValueError(ERROR_MESSAGES['INVALID_IMAGE_FILE'])
            
            # Save image to student's directory
            student_dir = get_student_faces_path(student.student_code)
            filename = f"{student.student_code}_{current_images + 1}_{int(datetime.utcnow().timestamp())}.jpg"
            image_path = os.path.join(student_dir, filename)
            
            # Save the file
            image_file.save(image_path)
            
            # Create database record
            image = StudentImage(
                student_id=student_id,
                image_url=f"/uploads/student_faces/{student.student_code}/{filename}",
                image_path=image_path,
                angle=angle,
                quality_score=quality_score,
                uploaded_by_id=uploaded_by_id,
                is_valid=True
            )
            db.session.add(image)
            db.session.commit()
            
            # Update student's face recognition status
            student.update_face_recognition_status()
            db.session.commit()
            
            logger.info(f'Face image added for student: {student.student_code}')
            return image
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error adding image for student {student_id}: {str(e)}')
            raise
    
    @staticmethod
    def invalidate_student_image(image_id):
        image = db.session.query(StudentImage).get(image_id)
        if not image:
            raise ValueError("Image not found")
        
        image.is_valid = False
        db.session.commit()
        
        student = image.student
        student.update_face_recognition_status()
        db.session.commit()
        return image
    
    @staticmethod
    def delete_student_image(image_id):
        image = db.session.query(StudentImage).get(image_id)
        if not image:
            raise ValueError("Image not found")
        
        student_id = image.student_id
        image_path = image.image_path
        
        db.session.delete(image)
        db.session.commit()
        
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            pass
        
        student = StudentService.get_student_by_id(student_id)
        if student:
            student.update_face_recognition_status()
            db.session.commit()
        
        return True
    
    @staticmethod
    def can_delete_student(student_id):
        student = StudentService.get_student_by_id(student_id)
        if not student:
            return False, "Student not found"
        
        if not student.can_delete():
            return False, "Cannot delete: This student has attendance records"
        
        return True, "Can delete"
    
    @staticmethod
    def deactivate_student(student_id):
        student = StudentService.get_student_by_id(student_id)
        if not student:
            raise ValueError("Student not found")
        
        student.is_active = False
        db.session.commit()
        return student
    
    @staticmethod
    def activate_student(student_id):
        student = StudentService.get_student_by_id(student_id)
        if not student:
            raise ValueError("Student not found")
        
        student.is_active = True
        db.session.commit()
        return student
