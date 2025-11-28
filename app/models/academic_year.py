from datetime import datetime
from app import db


class AcademicYear(db.Model):
    __tablename__ = 'academic_years'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(9), unique=True, nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    classrooms = db.relationship('ClassRoom', backref='academic_year', lazy='dynamic', cascade='all, delete-orphan')
    
    def activate(self):
        old_active = db.session.query(AcademicYear).filter_by(is_active=True).first()
        if old_active:
            old_active.is_active = False
        self.is_active = True
    
    def can_delete(self):
        return self.classrooms.count() == 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_active': self.is_active,
            'classroom_count': self.classrooms.count(),
            'created_at': self.created_at,
        }
    
    def __repr__(self):
        return f'<AcademicYear {self.year}>'
