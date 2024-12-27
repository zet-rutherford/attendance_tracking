from app.extensions import db, logger
from app.models import AttendanceRecord
from app.services.feature_service import FeatureService
from datetime import datetime, timedelta
import os
from sqlalchemy import func

class RecordService:
    def __init__(self):
        self.feature_service = FeatureService()
        self.max_distance = int(os.getenv('ATTENDANCE_MAX_DISTANCE', 5000))

    def get_daily_records(self, user_id, date=None):
        """Get user's attendance records for a specific date"""
        if date is None:
            date = datetime.now().date()
            
        return AttendanceRecord.query.filter(
            AttendanceRecord.user_id == user_id,
            func.date(AttendanceRecord.check_time) == date
        ).order_by(AttendanceRecord.check_time).all()

    def has_checked_in_today(self, user_id):
        """Check if user has already checked in today"""
        today = datetime.now().date()
        return AttendanceRecord.query.filter(
            AttendanceRecord.user_id == user_id,
            AttendanceRecord.check_type == 'IN',
            func.date(AttendanceRecord.check_time) == today
        ).first() is not None

    def has_checked_out_today(self, user_id):
        """Check if user has already checked out today"""
        today = datetime.now().date()
        return AttendanceRecord.query.filter(
            AttendanceRecord.user_id == user_id,
            AttendanceRecord.check_type == 'OUT',
            func.date(AttendanceRecord.check_time) == today
        ).first() is not None

    def create_attendance_record(self, user_id, check_type, similarity, distance, device_info=None):
        """Create and save attendance record with validation"""
        # Check existing records
        if check_type == 'IN' and self.has_checked_in_today(user_id):
            raise ValueError('Already checked in today')
        if check_type == 'OUT' and self.has_checked_out_today(user_id):
            raise ValueError('Already checked out today')
            
        # For check-out, verify that user has checked in
        if check_type == 'OUT' and not self.has_checked_in_today(user_id):
            raise ValueError('Must check in before checking out')

        is_valid = (similarity >= self.feature_service.similarity_threshold and 
                   distance <= self.max_distance)
        
        record = AttendanceRecord(
            user_id=user_id,
            check_time=datetime.utcnow(),
            check_type=check_type,
            face_similarity=similarity,
            location=distance,
            device_info=device_info,
            status='SUCCESS' if is_valid else 'FAILED'
        )
        
        db.session.add(record)
        db.session.commit()
        
        return record

    def process_attendance(self, user_id, image_file, distance, device_info, check_type='IN'):
        """Process complete attendance check-in/out"""
        try:
            # Verify face
            similarity, is_valid = self.feature_service.verify_face(user_id, image_file)
            
            # Create record
            record = self.create_attendance_record(
                user_id=user_id,
                check_type=check_type,
                similarity=similarity,
                distance=distance,
                device_info=device_info
            )
            
            return record, similarity
        except Exception as e:
            logger.error(f"Attendance processing error: {str(e)}")
            raise