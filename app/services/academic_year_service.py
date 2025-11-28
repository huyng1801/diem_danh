from app import db
from app.models.academic_year import AcademicYear
from app.utils.validators import is_valid_academic_year
from app.utils.constants import ERROR_MESSAGES
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AcademicYearService:
    
    @staticmethod
    def validate_year_format(year):
        """
        Validate academic year format using utils validator
        """
        if not is_valid_academic_year(year):
            raise ValueError(ERROR_MESSAGES['INVALID_ACADEMIC_YEAR'])
        return True
    
    @staticmethod
    def create_academic_year(year, start_date, end_date):
        try:
            AcademicYearService.validate_year_format(year)
            
            if db.session.query(AcademicYear).filter_by(year=year).first():
                raise ValueError("Academic year already exists")
            
            if end_date <= start_date:
                raise ValueError("End date must be after start date")
            
            academic_year = AcademicYear(
                year=year,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(academic_year)
            db.session.commit()
            
            logger.info(f'Academic year created successfully: {year}')
            return academic_year
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error creating academic year {year}: {str(e)}')
            raise
    
    @staticmethod
    def get_academic_year_by_id(year_id):
        return db.session.query(AcademicYear).filter_by(id=year_id).first()
    
    @staticmethod
    def get_academic_year_by_year(year):
        return db.session.query(AcademicYear).filter_by(year=year).first()
    
    @staticmethod
    def get_all_academic_years():
           return db.session.query(AcademicYear).order_by(AcademicYear.start_date, AcademicYear.end_date).all()
    
    @staticmethod
    def get_active_academic_year():
        return db.session.query(AcademicYear).filter_by(is_active=True).first()
    
    @staticmethod
    def activate_academic_year(year_id):
        academic_year = AcademicYearService.get_academic_year_by_id(year_id)
        if not academic_year:
            raise ValueError("Academic year not found")
        
        old_active = AcademicYearService.get_active_academic_year()
        if old_active:
            old_active.is_active = False
        
        academic_year.is_active = True
        db.session.commit()
        return academic_year
    
    @staticmethod
    def update_academic_year(year_id, **kwargs):
        from datetime import datetime
        academic_year = AcademicYearService.get_academic_year_by_id(year_id)
        if not academic_year:
            raise ValueError("Academic year not found")
        
        # Convert string dates to datetime objects if needed
        if 'start_date' in kwargs and isinstance(kwargs['start_date'], str):
            try:
                kwargs['start_date'] = datetime.strptime(kwargs['start_date'], '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Invalid start_date format. Use YYYY-MM-DD")
        
        if 'end_date' in kwargs and isinstance(kwargs['end_date'], str):
            try:
                kwargs['end_date'] = datetime.strptime(kwargs['end_date'], '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Invalid end_date format. Use YYYY-MM-DD")
        
        if 'start_date' in kwargs and 'end_date' in kwargs:
            if kwargs['end_date'] <= kwargs['start_date']:
                raise ValueError("End date must be after start date")
        
        # Allow updating year, start_date, end_date
        allowed_fields = ['year', 'start_date', 'end_date']
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(academic_year, key, value)

        # If is_active is set to True, deactivate all others and activate this one
        if 'is_active' in kwargs and kwargs['is_active']:
            old_active = AcademicYearService.get_active_academic_year()
            if old_active and old_active.id != academic_year.id:
                old_active.is_active = False
            academic_year.is_active = True
        elif 'is_active' in kwargs:
            academic_year.is_active = False

        db.session.commit()
        return academic_year
    
    @staticmethod
    def can_delete_academic_year(year_id):
        academic_year = AcademicYearService.get_academic_year_by_id(year_id)
        if not academic_year:
            return False, "Academic year not found"
        
        if not academic_year.can_delete():
            return False, "Cannot delete: This academic year has classroom data"
        
        return True, "Can delete"
    
    @staticmethod
    def delete_academic_year(year_id):
        can_delete, message = AcademicYearService.can_delete_academic_year(year_id)
        if not can_delete:
            raise ValueError(message)
        
        academic_year = AcademicYearService.get_academic_year_by_id(year_id)
        db.session.delete(academic_year)
        db.session.commit()
        return True
    
    @staticmethod
    def deactivate_academic_year(year_id):
        academic_year = AcademicYearService.get_academic_year_by_id(year_id)
        if not academic_year:
            raise ValueError("Academic year not found")
        
        academic_year.is_active = False
        db.session.commit()
        return academic_year
