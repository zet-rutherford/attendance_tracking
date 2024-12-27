from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.services.user_service import UserService
from app.extensions import logger, redis_client, jwt
from datetime import datetime, timezone
from redis.exceptions import RedisError

bp = Blueprint('auth', __name__)
user_service = UserService()

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        required_fields = ['username', 'password', 'email', 'fullname']
        
        # Validate required fields
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
            
        # Check if username already exists
        if user_service.get_user_by_username(data['username']):
            return jsonify({
                'status': 'error',
                'message': 'Username already exists'
            }), 400
            
        # Create new user
        user = user_service.create_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            fullname=data['fullname'],
            phone=data.get('phone', '')
        )
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'fullname': user.fullname
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error in register: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'status': 'error',
                'message': 'Missing username or password'
            }), 400
            
        user = user_service.get_user_by_username(data['username'])
        
        if not user or not user_service.verify_password(data['password'], user.password):
            return jsonify({
                'status': 'error',
                'message': 'Invalid username or password'
            }), 401
            
        if not user.active:
            return jsonify({
                'status': 'error',
                'message': 'Account is deactivated'
            }), 401
            
        # Create access token with fresh JTI
        access_token = create_access_token(
            identity=user.id,
            additional_claims={"type": "access"})
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'fullname': user.fullname
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

# Add this at the top of the file after imports
def check_redis_connection():
    """Check if Redis is available"""
    try:
        if redis_client is None:
            return False
        redis_client.ping()
        return True
    except RedisError:
        return False

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    """Check if the token has been blacklisted."""
    try:
        if not check_redis_connection():
            logger.warning("Redis unavailable, skipping blacklist check")
            return False
            
        jti = jwt_payload["jti"]
        token_in_redis = redis_client.get(jti)
        return token_in_redis is not None
    except RedisError as e:
        logger.error(f"Redis error in blacklist check: {str(e)}")
        # If Redis fails, accept the token
        return False

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        # Get token info
        jwt_payload = get_jwt()
        jti = jwt_payload["jti"]
        
        # Calculate token's remaining lifetime
        exp_timestamp = jwt_payload['exp']
        current_timestamp = datetime.now(timezone.utc).timestamp()
        ttl = int(exp_timestamp - current_timestamp)
        
        # Add token to blacklist with expiration
        if ttl > 0:
            redis_client.setex(jti, ttl, 'blacklisted')
            
        return jsonify({
            'status': 'success',
            'message': 'Successfully logged out'
        }), 200
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error during logout'
        }), 500