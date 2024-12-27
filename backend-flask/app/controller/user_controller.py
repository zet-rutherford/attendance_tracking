from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import logger
from app.services.feature_service import FeatureService
import requests

bp = Blueprint('features', __name__)
feature_service = FeatureService()

@bp.route('/register-face', methods=['POST'])
@jwt_required()
def register_face():
    try:
        current_user_id = get_jwt_identity()
        
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided'
            }), 400
            
        image_file = request.files['image']
        
        face_feature = feature_service.register_face(
            user_id=current_user_id,
            image_file=image_file
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Face registered successfully',
            'data': {
                'feature_id': face_feature.id,
                'user_id': current_user_id
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except requests.RequestException as e:
        logger.error(f"Failed to communicate with facial service: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to communicate with facial service'
        }), 500
        
    except Exception as e:
        logger.error(f"Error in register_face: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
    
@bp.route('/register-face-status', methods=['GET'])
@jwt_required()
def get_register_face_status():
    try:
        current_user_id = get_jwt_identity()
        
        register_feature = feature_service.get_active_face_feature(current_user_id)
        if register_feature:
            return jsonify({
            'status': 'success',
            'data': {
                'feature_status': "yes",
                'user_id': current_user_id
            }}), 200
        else:
            return jsonify({
            'status': 'success',
            'data': {
                'feature_status': "no",
                'user_id': current_user_id
            }}), 200
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except requests.RequestException as e:
        logger.error(f"Failed to communicate with facial service: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to communicate with facial service'
        }), 500
        
    except Exception as e:
        logger.error(f"Error in register_face: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@bp.route('/verify-face', methods=['POST'])
@jwt_required()
def verify_face():
    try:
        current_user_id = get_jwt_identity()
        
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided'
            }), 400
            
        image_file = request.files['image']
        
        similarity, is_valid = feature_service.verify_face(
            user_id=current_user_id,
            image_file=image_file
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'similarity': similarity,
                'is_valid': is_valid,
                'user_id': current_user_id
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except requests.RequestException as e:
        logger.error(f"Failed to communicate with facial service: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to communicate with facial service'
        }), 500
        
    except Exception as e:
        logger.error(f"Error in verify_face: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500