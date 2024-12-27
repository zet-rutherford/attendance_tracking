from flask import Flask, Blueprint, jsonify
from flask_cors import CORS
from app.extensions import db, jwt, migrate
from .extensions import config, logger
# from app.utils.auth import JWTError

def create_app():
    """Application factory function"""
    logger.debug('Starting application creation')  # Add this
    
    app = Flask(__name__)
    logger.debug('Flask app instance created')  # Add this
    
    # Config
    app.url_map.strict_slashes = False
    app.config.from_object(config)
    logger.debug('Configuration loaded')  # Add this
    
    # Initialize extensions
    register_extensions(app)
    logger.debug('Extensions registered')
    
    # Register blueprints
    register_blueprints(app)
    logger.debug('Blueprints registered')
    
    # Register error handlers
    register_error_handlers(app)
    logger.debug('Error handlers registered')
    
    # Enable CORS
    CORS(app)
    logger.debug('CORS enabled')
    
    return app

def register_extensions(app):
    """Register Flask extensions."""
    logger.debug('Initializing SQLAlchemy')
    db.init_app(app)
    
    logger.debug('Initializing Flask-Migrate')
    migrate.init_app(app, db)
    
    logger.debug('Initializing JWT')
    jwt.init_app(app)
    
    logger.debug('Creating database tables')
    with app.app_context():
        db.create_all()

def register_blueprints(app):
    """Register Flask blueprints."""
    # Health check route
    health = Blueprint('health', __name__)
    @health.route('/ping', methods=['GET'])
    def ping():
        return jsonify(success=True, data="attendance service is healthy")
    
    app.register_blueprint(health)

    # Import and register API routes
    from app.controller.user_controller import bp as user_bp
    from app.controller.auth_controller import bp as auth_bp
    from app.controller.record_controller import bp as record_bp

    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(record_bp, url_prefix='/api/attendance')

def register_error_handlers(app):
    """Register error handlers."""
    
    # @app.errorhandler(JWTError)
    # def handle_jwt_error(error):
    #     response = jsonify(error.to_dict())
    #     response.status_code = error.status_code
    #     return response
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': 'Bad request',
            'details': str(error)
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': 'Resource not found',
            'details': str(error)
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error',
            'details': str(error)
        }), 500

def register_cli_commands(app):
    """Register CLI commands."""
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database."""
        db.create_all()
        print('Database initialized!')