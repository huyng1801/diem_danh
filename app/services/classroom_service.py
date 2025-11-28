from app import db
from app.models.class_room import ClassRoom
from app.models.student import Student
from app.models.academic_year import AcademicYear
from app.utils.validators import is_valid_grade, validate_classroom_data
from app.utils.constants import (
    ALLOWED_GRADES, MAX_STUDENTS_PER_CLASS, ERROR_MESSAGES
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ClassRoomService:
    
    @staticmethod
    def create_classroom(class_name, grade, academic_year_id, room_number=None, 
                        head_teacher_id=None, head_teacher=None, max_student=MAX_STUDENTS_PER_CLASS):
        try:
            if not AcademicYear.query.get(academic_year_id):
                raise ValueError("Academic year not found")
            
            # Validate grade
            if not is_valid_grade(grade):
                raise ValueError(f"Grade must be one of: {ALLOWED_GRADES}")
            
            existing = db.session.query(ClassRoom).filter_by(
                class_name=class_name,
                academic_year_id=academic_year_id
            ).first()
            
            if existing:
                raise ValueError("Classroom name already exists in this academic year")
            
            classroom = ClassRoom(
                class_name=class_name,
                grade=grade,
                academic_year_id=academic_year_id,
                room_number=room_number,
                head_teacher_id=head_teacher_id,
                head_teacher=head_teacher,
                max_student=max_student
            )
            db.session.add(classroom)
            db.session.commit()
            
            logger.info(f'Classroom created successfully: {class_name}')
            return classroom
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error creating classroom {class_name}: {str(e)}')
            raise
    
    @staticmethod
    def get_classroom_by_id(classroom_id):
        return db.session.query(ClassRoom).filter_by(id=classroom_id).first()
    
    @staticmethod
    def get_classrooms_by_academic_year(academic_year_id):
        return db.session.query(ClassRoom).filter_by(
            academic_year_id=academic_year_id,
            is_active=True
        ).order_by(ClassRoom.class_name).all()
    
    @staticmethod
    def get_classrooms_by_grade(academic_year_id, grade):
        return db.session.query(ClassRoom).filter_by(
            academic_year_id=academic_year_id,
            grade=grade,
            is_active=True
        ).order_by(ClassRoom.class_name).all()
    
    @staticmethod
    def get_all_classrooms(page=1, per_page=20):
        return db.session.query(ClassRoom).filter_by(is_active=True).order_by(ClassRoom.class_name).paginate(
            page=page, per_page=per_page
        )
    
    @staticmethod
    def update_classroom(classroom_id, **kwargs):
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        if not classroom:
            raise ValueError("Classroom not found")
        
        allowed_fields = ['class_name', 'grade', 'room_number', 'head_teacher_id', 
                         'head_teacher', 'max_student', 'is_active']
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'grade' and value not in ['6', '7', '8', '9']:
                    raise ValueError("Grade must be 6, 7, 8, or 9")
                setattr(classroom, key, value)
        
        classroom.updated_at = datetime.utcnow()
        db.session.commit()
        return classroom
    
    @staticmethod
    def get_classroom_students(classroom_id):
        return db.session.query(Student).filter_by(classroom_id=classroom_id).all()
    
    @staticmethod
    def get_classroom_student_count(classroom_id):
        return db.session.query(Student).filter_by(classroom_id=classroom_id).count()
    
    @staticmethod
    def is_classroom_full(classroom_id):
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        if not classroom:
            return False
        return classroom.is_full()
    
    @staticmethod
    def can_delete_classroom(classroom_id):
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        if not classroom:
            return False, "Classroom not found"
        
        if not classroom.can_delete():
            return False, "Cannot delete: This classroom has students"
        
        return True, "Can delete"
    
    @staticmethod
    def delete_classroom(classroom_id):
        can_delete, message = ClassRoomService.can_delete_classroom(classroom_id)
        if not can_delete:
            raise ValueError(message)
        
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        db.session.delete(classroom)
        db.session.commit()
        return True
    
    @staticmethod
    def deactivate_classroom(classroom_id):
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        if not classroom:
            raise ValueError("Classroom not found")
        
        classroom.is_active = False
        db.session.commit()
        return classroom
    
    @staticmethod
    def activate_classroom(classroom_id):
        classroom = ClassRoomService.get_classroom_by_id(classroom_id)
        if not classroom:
            raise ValueError("Classroom not found")
        
        classroom.is_active = True
        db.session.commit()
        return classroom
