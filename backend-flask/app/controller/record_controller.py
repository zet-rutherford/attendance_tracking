from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import logger
from datetime import datetime
from app.services.record_service import RecordService
import requests

bp = Blueprint('attendance', __name__)
record_service = RecordService()

@bp.route('/check-in', methods=['POST'])
@jwt_required()
def check_in():
    try:
        current_user_id = get_jwt_identity()
        # logger.debug("request:",request)
        
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided'
            }), 400
        
        distance = request.form.get('distance', type=int)
        if distance is None:
            return jsonify({
                'status': 'error',
                'message': 'Distance is required'
            }), 400
            
        device_info = request.form.get('device_info')
        image_file = request.files['image']
        
        record, similarity = record_service.process_attendance(
            user_id=current_user_id,
            image_file=image_file,
            distance=distance,
            device_info=device_info,
            check_type='IN'
        )
        
        response_data = {
            'record_id': record.id,
            'check_time': record.check_time.isoformat(),
            'similarity': similarity,
            'distance': distance,
            'status': record.status
        }
        
        if record.status == 'FAILED':
            return jsonify({
                'status': 'error',
                'message': 'Attendance check failed',
                'data': response_data
            }), 401
            
        return jsonify({
            'status': 'success',
            'message': 'Check-in successful',
            'data': response_data
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
        logger.error(f"Error in check_in: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@bp.route('/check-out', methods=['POST'])
@jwt_required()
def check_out():
    try:
        current_user_id = get_jwt_identity()
        
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided'
            }), 400
            
        distance = request.form.get('distance', type=int)
        if distance is None:
            return jsonify({
                'status': 'error',
                'message': 'Distance is required'
            }), 400
            
        device_info = request.form.get('device_info')
        image_file = request.files['image']
        
        record, similarity = record_service.process_attendance(
            user_id=current_user_id,
            image_file=image_file,
            distance=distance,
            device_info=device_info,
            check_type='OUT'
        )
        
        response_data = {
            'record_id': record.id,
            'check_time': record.check_time.isoformat(),
            'similarity': similarity,
            'distance': distance,
            'status': record.status
        }
        
        if record.status == 'FAILED':
            return jsonify({
                'status': 'error',
                'message': 'Attendance check failed',
                'data': response_data
            }), 401
            
        return jsonify({
            'status': 'success',
            'message': 'Check-out successful',
            'data': response_data
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
        logger.error(f"Error in check_out: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
    
@bp.route('/daily-records', methods=['GET'])
@jwt_required()
def get_daily_records():
    try:
        current_user_id = get_jwt_identity()
        date_str = request.args.get('date')  # Format: YYYY-MM-DD
        
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        else:
            date = None
            
        records = record_service.get_daily_records(current_user_id, date)
        
        return jsonify({
            'status': 'success',
            'data': [{
                'id': record.id,
                'check_type': record.check_type,
                'check_time': record.check_time.isoformat(),
                'face_similarity': record.face_similarity,
                'location': record.location,
                'status': record.status
            } for record in records]
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_daily_records: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500