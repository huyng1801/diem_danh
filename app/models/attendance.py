from datetime import datetime
from app import db


class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False, index=True)
    attendance_log_id = db.Column(db.Integer, db.ForeignKey('attendance_logs.id'), nullable=False)
    
    status = db.Column(db.String(20), default='present', index=True)
    check_in_time = db.Column(db.DateTime, nullable=True)  # Nullable for pre-created absent records
    check_in_image_url = db.Column(db.String(255))
    
    face_confidence = db.Column(db.Float, default=0.0)
    is_face_recognized = db.Column(db.Boolean, default=False)
    
    notes = db.Column(db.Text)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    classroom = db.relationship('ClassRoom')
    recorded_by = db.relationship('User', foreign_keys=[recorded_by_id])
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'attendance_log_id', name='unique_student_per_log'),
        db.Index('idx_date_classroom', 'created_at', 'classroom_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'status': self.status,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_in_image_url': self.check_in_image_url,
            'face_confidence': self.face_confidence,
            'is_face_recognized': self.is_face_recognized,
            'notes': self.notes,
            'created_at': self.created_at,
        }
    
    def __repr__(self):
        return f'<Attendance {self.id} - Student {self.student_id}>'
