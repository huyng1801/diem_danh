from datetime import datetime
from app import db


class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False, index=True)
    
    session_date = db.Column(db.Date, nullable=False, index=True)
    session_type = db.Column(db.String(20), default='morning', index=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    
    total_students = db.Column(db.Integer, default=0)
    present_count = db.Column(db.Integer, default=0)
    absent_count = db.Column(db.Integer, default=0)
    late_count = db.Column(db.Integer, default=0)
    excused_count = db.Column(db.Integer, default=0)
    
    is_finalized = db.Column(db.Boolean, default=False, index=True)
    
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    recorded_by = db.relationship('User', foreign_keys=[recorded_by_id])
    attendance_records = db.relationship('Attendance', backref='attendance_log', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('classroom_id', 'session_date', 'session_type', name='unique_session_per_classroom'),
        db.Index('idx_session_date_classroom', 'session_date', 'classroom_id'),
    )
    
    def calculate_statistics(self):
        from app.models.attendance import Attendance
        from app.models.student import Student
        
        # Get total active students in classroom (not from records)
        total_students = db.session.query(Student).filter_by(
            classroom_id=self.classroom_id,
            is_active=True
        ).count()
        
        # Update total_students if not set
        if self.total_students == 0 or self.total_students is None:
            self.total_students = total_students
        
        # Count attendance records by status
        records = db.session.query(Attendance).filter_by(attendance_log_id=self.id).all()
        
        self.present_count = sum(1 for r in records if r.status == 'present')
        self.absent_count = sum(1 for r in records if r.status == 'absent')
        self.late_count = sum(1 for r in records if r.status == 'late')
        self.excused_count = sum(1 for r in records if r.status == 'excused')
    
    def get_attendance_rate(self):
        if self.total_students == 0:
            return 0.0
        return (self.present_count / self.total_students) * 100
    
    def to_dict(self):
        return {
            'id': self.id,
            'classroom_id': self.classroom_id,
            'session_date': self.session_date.isoformat(),
            'session_type': self.session_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_students': self.total_students,
            'present_count': self.present_count,
            'absent_count': self.absent_count,
            'late_count': self.late_count,
            'excused_count': self.excused_count,
            'attendance_rate': self.get_attendance_rate(),
            'is_finalized': self.is_finalized,
            'created_at': self.created_at,
        }
    
    def __repr__(self):
        return f'<AttendanceLog {self.session_date} - {self.session_type}>'
