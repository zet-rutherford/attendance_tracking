from app.common.model import Log
from urllib.parse import urlparse

import time

from datetime import datetime
from app.controller.facial_service import auth_jwt as _jwt
import socket
from app.extensions import config # pragma: no cover
import requests
import cv2
import numpy as np
import json
import base64
from threading import Thread
from queue import Queue

def img2str(img):
    _, buffer = cv2.imencode('.jpg', img) # pragma: no cover
    image_base64 = base64.b64encode(buffer).decode('utf-8') # pragma: no cover
    return image_base64 # pragma: no cover

def get_diff_timestamp(tstamp1, tstamp2):
    if tstamp1 > tstamp2:
        td = tstamp1 - tstamp2
    else:
        td = tstamp2 - tstamp1
    return int(round(td.total_seconds()))

def get_log(log, trace_id, request, start_request, response_request, status_code):
    
    fmt = '%Y-%m-%d %H:%M:%S'
    now = datetime.now()

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
    # log.uid = client_id
    parsed_url = urlparse(request.url)

    log.urp = parsed_url.path
    log.urq = parsed_url.query
    if parsed_url.query != '':
        log.url = parsed_url.path + '?' + parsed_url.query
    else:
        log.url = parsed_url.path
    
    log.bbs = response_request.content_length
    log.st = status_code
    log.rt = round(time.time() - start_request, 3)

    return log


