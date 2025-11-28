from datetime import datetime
from app import db


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    parent_phone = db.Column(db.String(20))
    parent_name = db.Column(db.String(120))
    
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, index=True)
    avatar_url = db.Column(db.String(255))
    
    face_recognition_enabled = db.Column(db.Boolean, default=False)
    face_images_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    classroom = db.relationship('ClassRoom', backref='students')
    academic_year = db.relationship('AcademicYear')
    student_images = db.relationship('StudentImage', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def can_delete(self):
        return self.attendance_records.count() == 0
    
    def update_face_recognition_status(self):
        image_count = self.student_images.filter_by(is_valid=True).count()
        self.face_images_count = image_count
        self.face_recognition_enabled = image_count >= 3
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_code': self.student_code,
            'full_name': self.full_name,
            'gender': self.gender,
            'date_of_birth': self.date_of_birth.isoformat(),
            'address': self.address,
            'phone': self.phone,
            'parent_phone': self.parent_phone,
            'parent_name': self.parent_name,
            'classroom_id': self.classroom_id,
            'is_active': self.is_active,
            'avatar_url': self.avatar_url,
            'face_recognition_enabled': self.face_recognition_enabled,
            'face_images_count': self.face_images_count,
            'created_at': self.created_at,
        }
    
    def __repr__(self):
        return f'<Student {self.student_code} - {self.full_name}>'
