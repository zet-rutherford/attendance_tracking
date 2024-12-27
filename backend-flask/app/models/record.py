from datetime import datetime
from app.extensions import db

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_time = db.Column(db.DateTime, nullable=False)
    check_type = db.Column(db.String(10), nullable=False)  # 'IN' or 'OUT'
    face_similarity = db.Column(db.Float)
    location = db.Column(db.Integer)  # Distance in meters from check point
    device_info = db.Column(db.JSON)
    status = db.Column(db.String(20), default='SUCCESS')  # SUCCESS, FAILED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AttendanceRecord user_id={self.user_id} type={self.check_type}>'