from datetime import datetime
from app.extensions import db
import numpy as np

class FaceFeature(db.Model):
    __tablename__ = 'face_features'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feature_vector = db.Column(db.ARRAY(db.Float), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FaceFeature user_id={self.user_id}>'