# -*- coding: utf-8 -*-
import time
import os
import uuid
from datetime import datetime
import socket
import cv2
from flask import Blueprint, request, jsonify
import numpy
import json
import dataclasses
from urllib.parse import urlparse

from app.controller.facial_service import auth_jwt as _jwt
from ...common.model import Log
from ... import logger, config
from app.constants import *
from app.extensions import *
from app.controller.facial_service.utils import (
    get_log, img2str)
from app.controller.facial_service.algorithm import is_video_file

blueprint = Blueprint('facial-services', __name__)
supported_types = [
    "facial-recognition",
    "face-anti-spoofing",
    "face-anti-spoofing-video",
    "boundingbox-generator"
]
algorithms = dict()
# face_manager = FaceManager()

def init():  
   # Load all algorithms
    for name in supported_types:
        if name == "facial-recognition":
            from app.controller.facial_service import get_algorithm
            algorithms[name] = get_algorithm()
        elif name == "face-anti-spoofing":
            from app.controller.facial_service import get_algorithm_spoofing
            algorithms[name] = get_algorithm_spoofing()
        elif name == "boundingbox-generator":
            from app.controller.facial_service import gen_algorithm_boxgenerator
            algorithms[name] = gen_algorithm_boxgenerator()
        elif name == "face-anti-spoofing-video":
            from app.controller.facial_service import get_algorithm_spoofing_video
            algorithms[name] = get_algorithm_spoofing_video()

    print("=" * 80)
    print("FACIAL SERVICES INITIALIZED SUCCESSFULLY")
    print("=" * 80)

@blueprint.route('/face-align', methods=['POST'])
def face_align():
    start_request = time.time()
    trace_id = str(uuid.uuid1())
    log = Log(ex_trace_id=trace_id)

    try:
        start_time_decode = time.time()        
        image_file = request.files['image']
        img_np_array = numpy.fromfile(image_file, dtype='uint8')
        image = cv2.imdecode(img_np_array, cv2.IMREAD_COLOR)
        log.ex_time_decode_image = round(time.time() - start_time_decode, 3)
    
        status, aligned_face = algorithms['facial-recognition'].detect_biggest_face(image, log)
        if status == 0:
            response_request = jsonify(success=False, message=FACE_NOT_FOUND, trace_id=trace_id)
            get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_SUCCCES)
            logger.info(json.dumps(dataclasses.asdict(log)))
            return response_request, STATUS_CODE_SUCCCES

        aligned_face_bs64 = img2str(aligned_face)
        respone_data = {'aligned_face': aligned_face_bs64}
        response_request = jsonify(success=True, data=respone_data, trace_id=trace_id)
        # log.ex_image_align = aligned_face_bs64
        # get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_SUCCCES)
        # logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, STATUS_CODE_SUCCCES

    except Exception as e:
        response_request = jsonify(success=False, message="cannot detect face : {0}".format(e), trace_id=trace_id)
        log.rt = round(time.time() - start_request, 3)
        get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_ERROR)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, STATUS_CODE_ERROR

@blueprint.route('/search', methods=['POST'])
# @jwt_validate(allowed_scopes=[FACE_VALIDATION])
def search():
    start_request = time.time()
    trace_id = str(uuid.uuid1())
    log = Log(ex_trace_id=trace_id)

    try:        
        image_file = request.files['image']
        try:
            aligned = int(request.form['aligned'])
        except:
            aligned = 0
        start_time_decode = time.time()
        img_np_array = numpy.fromfile(image_file, dtype='uint8')
        image = cv2.imdecode(img_np_array, cv2.IMREAD_COLOR)
        log.ex_time_decode_image = round(time.time() - start_time_decode, 3)
        if aligned == 0:
            status, normalized_feature = algorithms['facial-recognition'].extract_feature(image, log)

            if status == 0:
                response_request = jsonify(success=False, message=FACE_NOT_FOUND, trace_id=trace_id)
                get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_SUCCCES)
                logger.info(json.dumps(dataclasses.asdict(log)))
                return response_request, STATUS_CODE_SUCCCES
        elif aligned == 1:
            normalized_feature = algorithms['facial-recognition'].extract_feature_non_detect(image, log)

        normalized_feature = numpy.reshape(normalized_feature[0], (1, -1))
        result_score, result_username = face_manager.recognition(normalized_feature ,log)

        if result_username == CANNOT_IDENTIFY:
            respone_data = result_username
            response_request = jsonify(success=False, msg=respone_data, trace_id=trace_id)
            log.ex_username = result_username           
        else:
            respone_data = {'username': result_username, 'score': result_score}
            response_request = jsonify(success=True, data=respone_data, trace_id=trace_id)
            log.ex_username = result_username
            log.ex_score_search = result_score

        get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_SUCCCES)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, STATUS_CODE_SUCCCES

    except Exception as e:
        response_request = jsonify(success=False, message="cannot extract feature : {0}".format(e), trace_id=trace_id)
        log.ex_msg_exception = str(e)
        get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_ERROR)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, STATUS_CODE_ERROR

@blueprint.route('/face-matching', methods=['POST'])
# @jwt_validate(allowed_scopes=[FACE_VALIDATION])
def face_matching():
    start_request = time.time()
    trace_id = str(uuid.uuid1())
    log = Log(ex_trace_id=trace_id)

    try:
        start_time_decode = time.time()
        image_file_1 = request.files['image_1']
        image_file_2 = request.files['image_2']
        img_np_array_1 = numpy.fromfile(image_file_1, dtype='uint8')
        image_1 = cv2.imdecode(img_np_array_1, cv2.IMREAD_COLOR)

        img_np_array_2 = numpy.fromfile(image_file_2, dtype='uint8')
        image_2 = cv2.imdecode(img_np_array_2, cv2.IMREAD_COLOR)
        log.ex_time_decode_image = round(time.time() - start_time_decode, 3)

        status_1, normalized_feature_1 = algorithms['facial-recognition'].extract_feature(image_1, log)
        status_2, normalized_feature_2 = algorithms['facial-recognition'].extract_feature(image_2, log)

        if status_1 == 0 or status_2 == 0:
            response_request = jsonify(success=False, message=FACE_NOT_FOUND, trace_id=trace_id)
            get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_SUCCCES)
            logger.info(json.dumps(dataclasses.asdict(log)))
            return response_request, STATUS_CODE_SUCCCES
        similary = numpy.dot(normalized_feature_1[0].tolist(), normalized_feature_2[0].tolist())
        similary = round(similary, 3)
        respone_data = {'similarity': similary}
        response_request = jsonify(success=True, data=respone_data, trace_id=trace_id)
     
        log.ex_score_matching = similary
        get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_SUCCCES)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, STATUS_CODE_SUCCCES

    except Exception as e:
        response_request = jsonify(success=False, message="cannot extract feature : {0}".format(e), trace_id=trace_id)
        log.ex_msg_exception = str(e)
        get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_ERROR)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, STATUS_CODE_ERROR


@blueprint.route('/extract-feature', methods=['POST'])
# @jwt_validate(allowed_scopes=[FACE_VALIDATION])
def extract_feature():
    start_request = time.time()
    trace_id = str(uuid.uuid1())
    log = Log(ex_trace_id=trace_id)

    try:
        start_time_decode = time.time()        
        image_file = request.files['image']
        img_np_array = numpy.fromfile(image_file, dtype='uint8')
        image = cv2.imdecode(img_np_array, cv2.IMREAD_COLOR)
        log.ex_time_decode_image = round(time.time() - start_time_decode, 3)

        status, normalized_feature = algorithms['facial-recognition'].extract_feature(image, log)
        if status == 0:
            response_request = jsonify(success=False, message=FACE_NOT_FOUND, trace_id=trace_id)
            get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_SUCCCES)
            logger.info(json.dumps(dataclasses.asdict(log)))
            return response_request, STATUS_CODE_SUCCCES

        normalized_feature_string = str(normalized_feature[0].tolist())[1:-1].replace(' ', '')
        respone_data = {'normalized_feature': normalized_feature_string}
        response_request = jsonify(success=True, data=respone_data, trace_id=trace_id)
        log.ex_feature = normalized_feature_string
        get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_SUCCCES)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, STATUS_CODE_SUCCCES

    except Exception as e:
        response_request = jsonify(success=False, message="cannot extract feature : {0}".format(e), trace_id=trace_id)
        log.ex_msg_exception = str(e)
        get_log(log, trace_id, request, start_request, response_request, STATUS_CODE_ERROR)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, STATUS_CODE_ERROR
    
@blueprint.route('/detect-spoofing-image', methods=['POST'])
def detect_spoofing():
    start_request = time.time()
    trace_id = str(uuid.uuid1())
    fmt = '%Y-%m-%d %H:%M:%S'
    now = datetime.now()

    log = Log(ex_trace_id=trace_id)
    log.tl = now.strftime(fmt)
    log.rid = trace_id
    log.sn = socket.gethostname()
    log.host = request.headers['Host'] if 'Host' in request.headers.keys() else ''
    log.ua = request.headers['User-Agent'] if 'User-Agent' in request.headers.keys() else ''
    log.rf = request.headers['http_referer'] if 'http_referer' in request.headers.keys() else ''
    log.cl = int(request.headers['Content-Length']) if 'Content-Length' in request.headers.keys() else 0
    log.cip = request.headers['X-Real-Ip'] if 'X-Real-Ip' in request.headers.keys() else ''
    log.rmip = request.remote_addr
    log.mt = request.method
    log.url = request.url

    parsed_url = urlparse(request.url)
    log.urp = parsed_url.path
    log.urq = parsed_url.query
    if parsed_url.query != '':
        log.url = parsed_url.path + '?' + parsed_url.query
    else:
        log.url = parsed_url.path

    try:
        start_time_decode_image = time.time()
        face_image = request.files['face_image']

        face_image = numpy.fromfile(face_image, dtype='uint8')
        face_image = cv2.imdecode(face_image, cv2.IMREAD_COLOR)

        log.ex_time_decode_image = time.time() - start_time_decode_image

        t_start_predict = time.time()
        result = algorithms['face-anti-spoofing'].predict(face_image)
        log.ex_time_detect_spoofing = time.time() - t_start_predict
        log.rt = round(time.time() - start_request, 3)
        response_request = jsonify(success=True, data=result, trace_id=trace_id)
        log.bbs = response_request.content_length
        status_res = 200 if result['error_code'] == '' else 400
        log.st = status_res
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, status_res
    
    except Exception as e:
        response_request = jsonify(success=False, message="exeption : {0}".format(e), trace_id=trace_id)
        log.bbs = response_request.content_length
        log.st = 400
        log.rt = round(time.time() - start_request, 3)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, 400
    
@blueprint.route('/detect-spoofing-video', methods=['POST'])
def anti_spoofing_face():
    start_request = time.time()
    trace_id = str(uuid.uuid1())
    fmt = '%Y-%m-%d %H:%M:%S'
    now = datetime.now()

    log = Log(ex_trace_id=trace_id)
    log.tl = now.strftime(fmt)
    log.rid = trace_id
    log.sn = socket.gethostname()
    log.host = request.headers['Host'] if 'Host' in request.headers.keys() else ''
    log.ua = request.headers['User-Agent'] if 'User-Agent' in request.headers.keys() else ''
    log.rf = request.headers['http_referer'] if 'http_referer' in request.headers.keys() else ''
    log.cl = int(request.headers['Content-Length']) if 'Content-Length' in request.headers.keys() else 0
    log.cip = request.headers['X-Real-Ip'] if 'X-Real-Ip' in request.headers.keys() else ''
    log.rmip = request.remote_addr
    log.mt = request.method
    log.url = request.url

    parsed_url = urlparse(request.url)
    log.urp = parsed_url.path
    log.urq = parsed_url.query
    if parsed_url.query != '':
        log.url = parsed_url.path + '?' + parsed_url.query
    else:
        log.url = parsed_url.path

    InputForm_list = ['video']

    results_schema = {
        'label': '',
        'message': '',
        'score': 0,
        'image_face_base64': '',
        'error_code': ''
    }

    try:
        for elm_form in InputForm_list:
            # Receive  input
            if elm_form not in request.files and elm_form not in request.form:
                results_schema['message'] = f"No {elm_form} data provided"
                results_schema['error_code'] = LACK_DATA
                response_request = jsonify(success=False, data=results_schema, trace_id=trace_id)
                log.bbs = response_request.content_length
                log.st = 400
                log.ex_message = results_schema['message']
                log.ex_error_code = results_schema['error_code']
                log.rt = round(time.time() - start_request, 3)
                logger.info(json.dumps(dataclasses.asdict(log)))
                return response_request, 400

        video = request.files['video']
        is_pose_check = 0
        try:
            is_test = int(request.form['is_test'])
            is_pose_check = int(request.form['is_pose_check'])
        except Exception as ee: # pragma: no cover
            pass # pragma: no cover
        
        log.ex_is_pose_check = is_pose_check

        if not is_video_file(video):
            results_schema['message'] = "video invalid"
            results_schema['error_code'] = VIDEO_INVALID
            response_request = jsonify(success=False, data=results_schema, trace_id=trace_id)
            log.bbs = response_request.content_length
            log.st = 400
            log.ex_message = results_schema['message']
            log.ex_error_code = results_schema['error_code']
            log.rt = round(time.time() - start_request, 3)
            logger.info(json.dumps(dataclasses.asdict(log)))
            return response_request, 400

        # call logic at here
        result, image_upload, frame_upload = algorithms['face-anti-spoofing-video'].predict(video, log, results_schema, is_pose_check)
        status_res = 200 if result['error_code'] == '' else 400
        log.rt = round(time.time() - start_request, 3)
        response_request = jsonify(success=True, data=result, trace_id=trace_id)
        log.bbs = response_request.content_length
        log.st = status_res
        log.ex_score = result['score']
        log.ex_label = result['label']
        log.ex_message = result['message']
        log.ex_error_code = result['error_code']
        logger.info(json.dumps(dataclasses.asdict(log)))


        return response_request, status_res
    
    except Exception as e:
        results_schema['message'] = "exception : {0}".format(e) # pragma: no cover
        results_schema['error_code'] = EXCEPTION_REQUEST # pragma: no cover
        response_request = jsonify(success=False, data=results_schema, trace_id=trace_id)
        log.bbs = response_request.content_length
        log.st = 400
        log.ex_message = results_schema['message'] # pragma: no cover
        log.ex_error_code = results_schema['error_code'] # pragma: no cover
        log.rt = round(time.time() - start_request, 3)
        logger.info(json.dumps(dataclasses.asdict(log)))
        return response_request, 400