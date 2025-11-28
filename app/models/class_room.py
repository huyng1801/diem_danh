from datetime import datetime
from app import db


class ClassRoom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False, index=True)
    grade = db.Column(db.String(10), nullable=False)
    room_number = db.Column(db.String(20))
    head_teacher = db.Column(db.String(120))
    head_teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    
    student_count = db.Column(db.Integer, default=0)
    max_student = db.Column(db.Integer, default=45)
    
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    head_teacher_obj = db.relationship('User', foreign_keys=[head_teacher_id])
    attendance_sessions = db.relationship('AttendanceLog', backref='classroom', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('class_name', 'academic_year_id', name='unique_class_per_year'),
    )
    
    def update_student_count(self):
        from app.models.student import Student
        self.student_count = db.session.query(db.func.count(Student.id)).filter(
            Student.classroom_id == self.id
        ).scalar() or 0
    
    def can_delete(self):
        from app.models.student import Student
        return db.session.query(Student).filter_by(classroom_id=self.id).count() == 0
    
    def is_full(self):
        return self.student_count >= self.max_student
    
    def to_dict(self):
        return {
            'id': self.id,
            'class_name': self.class_name,
            'grade': self.grade,
            'room_number': self.room_number,
            'head_teacher': self.head_teacher,
            'student_count': self.student_count,
            'max_student': self.max_student,
            'is_active': self.is_active,
            'created_at': self.created_at,
        }
    
    def __repr__(self):
        return f'<ClassRoom {self.class_name}>'
