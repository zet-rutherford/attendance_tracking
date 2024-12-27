from app.extensions import db, logger
import requests
import os
import numpy as np
from app.models import FaceFeature

class FeatureService:
    def __init__(self):
        self.facial_service_url = os.getenv('FACIAL_SERVICE_URL')
        self.similarity_threshold = float(os.getenv('FACE_SIMILARITY_THRESHOLD', 0.5))

    def check_face_spoofing(self, image_file):
        """Check if face is real using anti-spoofing service"""
        try:
            spoofing_url = f"{self.facial_service_url}/facial-service/detect-spoofing-image"
            files = {'face_image': (image_file.filename, image_file.read(), image_file.content_type)}
            
            response = requests.post(spoofing_url, files=files)
            response.raise_for_status()
            
            spoof_data = response.json()
            if not spoof_data.get('success') or spoof_data.get('data', {}).get('error_code') != '':
                raise ValueError('Anti-spoofing check failed')
                
            return True
        except Exception as e:
            logger.error(f"Spoofing check error: {str(e)}")
            raise

    def extract_face_features(self, image_file):
        """Extract features from face image"""
        try:
            extract_url = f"{self.facial_service_url}/facial-service/extract-feature"
            files = {'image': (image_file.filename, image_file.read(), image_file.content_type)}
            
            response = requests.post(extract_url, files=files)
            response.raise_for_status()
            
            feature_data = response.json()
            if not feature_data.get('success'):
                raise ValueError('Face feature extraction failed')
                
            return feature_data['data']['normalized_feature']
        except Exception as e:
            logger.error(f"Feature extraction error: {str(e)}")
            raise

    def calculate_similarity(self, stored_feature, current_feature):
        """Calculate cosine similarity between feature vectors"""
        try:
            if isinstance(stored_feature, str):
                stored_feature = [float(x) for x in stored_feature.split(',')]
            if isinstance(current_feature, str):
                current_feature = [float(x) for x in current_feature.split(',')]
                
            stored_array = np.array(stored_feature)
            current_array = np.array(current_feature)
            
            similarity = np.dot(stored_array, current_array)
            return round(float(similarity), 3)
        except Exception as e:
            logger.error(f"Similarity calculation error: {str(e)}")
            raise

    def get_active_face_feature(self, user_id):
        """Get user's active face feature"""
        return FaceFeature.query.filter_by(
            user_id=user_id,
            is_active=True
        ).first()

    def register_face(self, user_id, image_file):
        """Register new face for user"""
        try:
            # Check anti-spoofing first
            image_file.seek(0)
            self.check_face_spoofing(image_file)
            
            # Extract features
            image_file.seek(0)
            feature_string = self.extract_face_features(image_file)
            feature_array = [float(x) for x in feature_string.split(',')]
            
            # Deactivate previous features
            FaceFeature.query.filter_by(
                user_id=user_id,
                is_active=True
            ).update({'is_active': False})
            
            # Create new feature
            face_feature = FaceFeature(
                user_id=user_id,
                feature_vector=feature_array,
                is_active=True
            )
            
            db.session.add(face_feature)
            db.session.commit()
            
            return face_feature
        except Exception as e:
            db.session.rollback()
            logger.error(f"Face registration error: {str(e)}")
            raise

    def verify_face(self, user_id, image_file):
        """Verify face against stored feature"""
        try:
            # Check anti-spoofing
            image_file.seek(0)
            self.check_face_spoofing(image_file)
            
            # Get stored feature
            stored_feature = self.get_active_face_feature(user_id)
            if not stored_feature:
                raise ValueError('No registered face found')
            
            # Extract current features
            image_file.seek(0)
            current_feature = self.extract_face_features(image_file)
            
            # Calculate similarity
            similarity = self.calculate_similarity(
                stored_feature.feature_vector,
                current_feature
            )
            
            return similarity, similarity >= self.similarity_threshold
        except Exception as e:
            logger.error(f"Face verification error: {str(e)}")
            raise