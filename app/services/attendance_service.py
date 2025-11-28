from app import db
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.student import Student
from app.models.class_room import ClassRoom
from app.utils.validators import (
    is_valid_attendance_status, is_valid_session_type, 
    is_valid_confidence_score, validate_attendance_data
)
from app.utils.constants import (
    ATTENDANCE_STATUSES, MIN_FACE_CONFIDENCE, ERROR_MESSAGES,
    AUTO_MARK_ABSENT_HOURS
)
from app.utils.helpers import ensure_upload_directories
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class AttendanceService:
    
    @staticmethod
    def create_or_get_attendance_log(classroom_id, session_date, session_type='morning', 
                                     start_time=None, recorded_by_id=None):
        try:
            classroom = db.session.query(ClassRoom).get(classroom_id)
            if not classroom:
                raise ValueError(ERROR_MESSAGES['CLASSROOM_NOT_FOUND'])
            
            # Validate session type
            if not is_valid_session_type(session_type):
                raise ValueError("Invalid session type")
            
            log = db.session.query(AttendanceLog).filter_by(
                classroom_id=classroom_id,
                session_date=session_date,
                session_type=session_type
            ).first()
            
            if not log:
                # Get total active students in classroom
                total_students = db.session.query(Student).filter_by(
                    classroom_id=classroom_id,
                    is_active=True
                ).count()
                
                log = AttendanceLog(
                    classroom_id=classroom_id,
                    session_date=session_date,
                    session_type=session_type,
                    start_time=start_time or datetime.now(),
                    recorded_by_id=recorded_by_id,
                    total_students=total_students
                )
                db.session.add(log)
                db.session.commit()
                logger.info(f'Attendance log created for classroom {classroom_id}, session {session_type} - Total students: {total_students}')
            
            return log
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error creating attendance log: {str(e)}')
            raise
    
    @staticmethod
    def record_attendance(student_id, attendance_log_id, status='present', 
                         face_confidence=0.0, is_face_recognized=False, 
                         check_in_image_url=None, recorded_by_id=None, notes=None):
        try:
            student = db.session.query(Student).get(student_id)
            if not student:
                raise ValueError(ERROR_MESSAGES['STUDENT_NOT_FOUND'])
            
            log = db.session.query(AttendanceLog).get(attendance_log_id)
            if not log:
                raise ValueError(ERROR_MESSAGES['ATTENDANCE_LOG_NOT_FOUND'])
            
            # Validate status
            if not is_valid_attendance_status(status):
                raise ValueError(ERROR_MESSAGES['INVALID_ATTENDANCE_STATUS'])
            
            # Validate confidence score if provided
            if face_confidence and not is_valid_confidence_score(face_confidence):
                raise ValueError("Invalid confidence score")
            
            # Check for duplicate attendance in same session
            existing = db.session.query(Attendance).filter_by(
                student_id=student_id,
                attendance_log_id=attendance_log_id
            ).first()
            
            if existing:
                logger.info(f'Student {student.student_code} already checked in, updating...')
                # Update existing record if confidence is higher
                if face_confidence > existing.face_confidence:
                    existing.face_confidence = face_confidence
                    existing.status = status
                    existing.updated_at = datetime.now()
                    db.session.commit()
                return existing
            
            # Business rule: Face recognition requires minimum confidence
            if is_face_recognized and face_confidence < MIN_FACE_CONFIDENCE:
                logger.warning(f'Low confidence {face_confidence} for student {student.student_code}')
            
            attendance = Attendance(
                student_id=student_id,
                classroom_id=log.classroom_id,
                attendance_log_id=attendance_log_id,
                status=status,
                check_in_time=datetime.now(),
                check_in_image_url=check_in_image_url,
                face_confidence=face_confidence,
                is_face_recognized=is_face_recognized,
                recorded_by_id=recorded_by_id,
                notes=notes
            )
            db.session.add(attendance)
            db.session.commit()
            
            logger.info(f'Attendance recorded for student {student.student_code}: {status}')
            return attendance
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error recording attendance: {str(e)}')
            raise
    
    @staticmethod
    def get_attendance_by_id(attendance_id):
        return db.session.query(Attendance).filter_by(id=attendance_id).first()
    
    @staticmethod
    def get_attendance_by_student_and_log(student_id, attendance_log_id):
        return db.session.query(Attendance).filter_by(
            student_id=student_id,
            attendance_log_id=attendance_log_id
        ).first()
    
    @staticmethod
    def get_session_attendance(attendance_log_id):
        return db.session.query(Attendance).filter_by(
            attendance_log_id=attendance_log_id
        ).all()
    
    @staticmethod
    def get_student_attendance_by_date(student_id, session_date):
        return db.session.query(Attendance).join(AttendanceLog).filter(
            Attendance.student_id == student_id,
            AttendanceLog.session_date == session_date
        ).all()
    
    @staticmethod
    def get_classroom_attendance_by_date(classroom_id, session_date, session_type=None):
        query = db.session.query(Attendance).join(AttendanceLog).filter(
            AttendanceLog.classroom_id == classroom_id,
            AttendanceLog.session_date == session_date
        )
        
        if session_type:
            query = query.filter(AttendanceLog.session_type == session_type)
        
        return query.all()
    
    @staticmethod
    def get_attendance_by_date_range(classroom_id, start_date, end_date):
        return db.session.query(Attendance).join(AttendanceLog).filter(
            AttendanceLog.classroom_id == classroom_id,
            AttendanceLog.session_date.between(start_date, end_date)
        ).all()
    
    @staticmethod
    def update_attendance_status(attendance_id, status, notes=None):
        attendance = AttendanceService.get_attendance_by_id(attendance_id)
        if not attendance:
            raise ValueError("Attendance record not found")
        
        allowed_statuses = ['present', 'absent', 'late', 'excused']
        if status not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        
        attendance.status = status
        if notes:
            attendance.notes = notes
        attendance.updated_at = datetime.utcnow()
        db.session.commit()
        return attendance
    
    @staticmethod
    def finalize_attendance_log(attendance_log_id):
        log = db.session.query(AttendanceLog).get(attendance_log_id)
        if not log:
            raise ValueError("Attendance log not found")
        
        # Get total active students in classroom - ensure accuracy
        total_students = db.session.query(Student).filter_by(
            classroom_id=log.classroom_id,
            is_active=True
        ).count()
        
        # Update total_students if it wasn't set or needs correction
        log.total_students = total_students
        
        log.calculate_statistics()
        log.is_finalized = True
        log.end_time = datetime.now()
        db.session.commit()
        
        logger.info(f'Attendance log finalized: {attendance_log_id} - Total students: {total_students}')
        return log
    
    @staticmethod
    def get_attendance_log_by_id(log_id):
        return db.session.query(AttendanceLog).filter_by(id=log_id).first()
    
    @staticmethod
    def mark_absent_unrecorded(classroom_id, session_date, session_type='morning'):
        try:
            classroom = db.session.query(ClassRoom).get(classroom_id)
            if not classroom:
                raise ValueError(ERROR_MESSAGES['CLASSROOM_NOT_FOUND'])
            
            # Get or create attendance log
            log = AttendanceService.create_or_get_attendance_log(
                classroom_id, session_date, session_type
            )
            
            # Get all students in classroom
            students = db.session.query(Student).filter_by(
                classroom_id=classroom_id, is_active=True
            ).all()
            
            marked_count = 0
            for student in students:
                # Check if student already has attendance record
                existing = db.session.query(Attendance).filter_by(
                    student_id=student.id,
                    attendance_log_id=log.id
                ).first()
                
                if not existing:
                    # Mark as absent
                    attendance = Attendance(
                        student_id=student.id,
                        attendance_log_id=log.id,
                        status='absent',
                        notes='Auto-marked absent after deadline'
                    )
                    db.session.add(attendance)
                    marked_count += 1
            
            db.session.commit()
            logger.info(f'Auto-marked {marked_count} students absent in classroom {classroom_id}')
            return marked_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error auto-marking absent: {str(e)}')
            raise
    
    @staticmethod
    def auto_mark_absent_after_deadline():
        """
        Auto-mark students absent after deadline (called by scheduler)
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=AUTO_MARK_ABSENT_HOURS)
            
            # Find unfinalized logs older than cutoff
            old_logs = db.session.query(AttendanceLog).filter(
                AttendanceLog.start_time <= cutoff_time,
                AttendanceLog.is_finalized == False
            ).all()
            
            total_marked = 0
            for log in old_logs:
                marked = AttendanceService.mark_absent_unrecorded(
                    log.classroom_id, log.session_date, log.session_type
                )
                total_marked += marked
                
                # Finalize the log
                AttendanceService.finalize_attendance_log(log.id)
            
            logger.info(f'Auto-marking completed: {total_marked} students marked absent')
            return total_marked
            
        except Exception as e:
            logger.error(f'Error in auto-mark absent job: {str(e)}')
            raise
        
        log = AttendanceService.create_or_get_attendance_log(
            classroom_id, session_date, session_type
        )
        
        recorded_students = db.session.query(Attendance.student_id).filter_by(
            attendance_log_id=log.id
        ).all()
        recorded_ids = [s[0] for s in recorded_students]
        
        students_in_class = db.session.query(Student).filter_by(
            classroom_id=classroom_id,
            is_active=True
        ).all()
        
        for student in students_in_class:
            if student.id not in recorded_ids:
                AttendanceService.record_attendance(
                    student_id=student.id,
                    attendance_log_id=log.id,
                    status='absent'
                )
        
        return log
