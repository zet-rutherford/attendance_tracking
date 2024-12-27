from app.models.user import User
from app.models.face_feature import FaceFeature
from app.models.record import AttendanceRecord

# This ensures all models are imported when importing from app.models
__all__ = ['User', 'FaceFeature', 'AttendanceRecord']