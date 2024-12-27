import logging
import os
import pathlib
import sys
from datetime import datetime
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
# import numpy as np
# import base64
# from PIL import Image
# import io

# Load environment variables
load_dotenv()
env = load_dotenv('env.example')

# Setup paths
PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG_DIR = PACKAGE_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'app.log'

# Setup logging
FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler

def get_file_handler():
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(FORMATTER)
    return file_handler

def get_logger(logger_name):
    """Get logger with prepared handlers."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler())
    logger.propagate = False
    
    return logger

logger = get_logger(__name__)

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Initialize Redis
import redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

class Config:
    """Application configuration class"""
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # Face verification settings
    FACE_VERIFICATION_URL = os.getenv('FACE_VERIFICATION_URL')
    FACE_SIMILARITY_THRESHOLD = float(os.getenv('FACE_SIMILARITY_THRESHOLD', 0.85))
    
    # File upload settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    UPLOAD_FOLDER = os.path.join(PACKAGE_ROOT, 'uploads')

def allowed_file(filename):
    """Check if file extension is allowed"""
    from app.constants import ALLOWED_IMAGE_EXTENSIONS
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# Initialize config
config = Config()