import logging
import os
import pathlib
import sys
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import json
import requests
import time
import base64
import io
import cv2
from PIL import Image
from queue import Queue
import dataclasses
from app.common.model import LogUpload
from app.constants import IOTAI_VALIDATION

from dotenv import load_dotenv

env = load_dotenv()
env = load_dotenv('env.example')

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent

LOG_DIR = PACKAGE_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'app.log'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

FORMATTER = logging.Formatter("%(message)s")

def img2str(img):
    if img is None:
        return ""
    retval, buffer = cv2.imencode('.jpg', img)
    jpg_as_text = base64.b64encode(buffer)
    return jpg_as_text.decode("utf-8")

def str2img(image_base64):
    if len(image_base64) == 0:
        return None
    imgdata = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(imgdata))
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)

def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler

def get_logger(*, logger_name):
    """Get logger with prepared handlers."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # file_handler = logging.FileHandler(LOG_FILE)
    # file_handler.setLevel(logging.DEBUG)
    # file_handler.setFormatter(FORMATTER)

    # logger.addHandler(file_handler)
    logger.addHandler(get_console_handler())
    logger.propagate = False

    return logger


logger = get_logger(logger_name=__name__)


class ApplicationConfig:
    """Unified application configuration class"""

    # Face Detection Settings
    FACE_DETECTION_MODELPATH = os.environ.get('FACE_DETECTION_MODELPATH')
    FACE_DETECTION_MODEL_PATH = os.environ.get('FACE_DETECTION_MODEL_PATH')
    FACE_DETECTION_INDEX_GPU = int(os.environ.get('FACE_DETECTION_INDEX_GPU'))
    FACE_DETECTION_CONF = float(os.environ.get('FACE_DETECTION_CONF'))
    FACE_DETECTION_IOU = float(os.environ.get('FACE_DETECTION_IOU'))
    FACE_DETECTION_IMAGESIZE = int(os.environ.get('FACE_DETECTION_IMAGESIZE'))
    FACE_DETECTION_CONF_THRES = float(os.environ.get('FACE_DETECTION_CONF_THRES'))
    FACE_DETECTION_INPUT_SIZE = int(os.environ.get('FACE_DETECTION_INPUT_SIZE'))
    MIN_SIZE_FACE = int(os.environ.get('MIN_SIZE_FACE'))

    # Face Recognition Settings
    FEATURE_EXTRACTION_MODEL_PATH = os.environ.get('FEATURE_EXTRACTION_MODEL_PATH')
    SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD'))

    # Anti-Spoofing Models
    USE_DEEPFAKE_MODEL = int(os.environ.get('USE_DEEPFAKE_MODEL'))
    FAS_MODEL_PATH_DEEP_FAKE = os.environ.get('FAS_MODEL_PATH_DEEP_FAKE')
    FAS_MODEL_PATH_1_0 = os.environ.get('FAS_MODEL_PATH_1_0')
    FAS_MODEL_PATH_2_7 = os.environ.get('FAS_MODEL_PATH_2_7')
    FAS_MODEL_PATH_4_0 = os.environ.get('FAS_MODEL_PATH_4_0')
    FAS_INDEX_GPU = int(os.environ.get('FAS_INDEX_GPU'))
    FAS_CONF_THRESHOLD = float(os.environ.get('FAS_CONF_THRESHOLD'))
    FAS_CONF_THRESHOLD_SUB_MODEL = float(os.environ.get('FAS_CONF_THRESHOLD_SUB_MODEL'))
    FAS_CONF_THRESHOLD_DEEPFAKE_MODEL = float(os.environ.get('FAS_CONF_THRESHOLD_DEEPFAKE_MODEL'))
    VOTE_THRESHOLD = float(os.environ.get('VOTE_THRESHOLD'))

    # GPU Configuration
    DEVICE_GPU = int(os.environ.get('DEVICE_GPU'))
    USE_GPU = DEVICE_GPU >= 0

    # Face Area Thresholds
    FACE_AREA_THRESHOLD_POSE = float(os.environ.get('FACE_AREA_THRESHOLD_POSE'))
    FACE_AREA_THRESHOLD_NO_POSE = float(os.environ.get('FACE_AREA_THRESHOLD_NO_POSE'))

    # Video Processing
    SKIP_FRAME = int(os.environ.get('SKIP_FRAME'))
    NUM_FRAME_CHECK = int(os.environ.get('NUM_FRAME_CHECK'))

    # Image Similarity Check
    THRESHOLD_DUPLICATE_IMAGE_SIMILARITY = float(os.environ.get('THRESHOLD_DUPLICATE_IMAGE_SIMILARITY'))
    THRESHOLD_DIFFERENT_IMAGE_SIMILARITY = float(os.environ.get('THRESHOLD_DIFFERENT_IMAGE_SIMILARITY'))
    NUMBER_CHECK_DUPLICATE = int(os.environ.get('NUMBER_CHECK_DUPLICATE'))

    # Redis Configuration
    REDIS_SERVER = os.environ.get('REDIS_SERVER')
    REDIS_SERVICE_NAME = os.environ.get('REDIS_SERVICE_NAME')
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')

# Initialize config
config = ApplicationConfig()

def get_diff_timestamp(tstamp1, tstamp2):
    if tstamp1 > tstamp2:
        td = tstamp1 - tstamp2
    else:
        td = tstamp2 - tstamp1
    return int(round(td.total_seconds()))
