from datetime import datetime
from app import db


class StudentImage(db.Model):
    __tablename__ = 'student_images'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    
    image_url = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    
    angle = db.Column(db.String(20))
    quality_score = db.Column(db.Float, default=0.0)
    
    is_valid = db.Column(db.Boolean, default=True, index=True)
    is_training = db.Column(db.Boolean, default=False)
    
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'image_url': self.image_url,
            'image_path': self.image_url,  # Use image_url for display
            'angle': self.angle,
            'quality_score': self.quality_score,
            'is_valid': self.is_valid,
            'is_training': self.is_training,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<StudentImage {self.id} - Student {self.student_id}>'
