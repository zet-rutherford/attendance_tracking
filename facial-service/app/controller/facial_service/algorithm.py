import random
import time
import mimetypes
import cv2
import tempfile
import numpy as np
import ffmpeg
import hashlib
import os
import threading
from skimage.metrics import structural_similarity
import concurrent.futures
from app.constants import *
from app.extensions import config
from app.controller.facial_service.utils import img2str
from app.gvision.face_detection import face_align

cv2.setNumThreads(8)

def get_diff_timestamp(tstamp1, tstamp2):
    if tstamp1 > tstamp2:
        td = tstamp1 - tstamp2
    else:
        td = tstamp2 - tstamp1
    return int(round(td.total_seconds()))

def is_video_file(file):
    mime_type, _ = mimetypes.guess_type(file.filename)
    return mime_type and mime_type.startswith('video')

class FaceRecognition:
    def __init__(self, feature_extractor, face_detector):
        self._feature_extractor = feature_extractor
        self._face_detector = face_detector

    def extract_feature(self, image, log):
        start_time_detect = time.time()
        status, aligned_face = self.detect_biggest_face(image, log)
        if status == 0:
            return status, FACE_NOT_FOUND
        log.ex_time_detection = round(time.time() - start_time_detect, 3)
        start_time_extract_feature = time.time()
        normalized_feature = self._feature_extractor(aligned_face)
        log.ex_time_extract_feature = round(time.time() - start_time_extract_feature, 3)
        return status, normalized_feature

    def extract_feature_non_detect(self, aligned_face, log):
        start_time_extract_feature = time.time()
        normalized_feature = self._feature_extractor(aligned_face)
        log.ex_time_extract_feature = round(time.time() - start_time_extract_feature, 3)
        return normalized_feature
    
    def detect_biggest_face(self, img, log):
        start_time_detect = time.time()
        status, bboxes, kpss = self._face_detector(img)
        if status == 0:
            return status, FACE_NOT_FOUND
            
        index = 0
        max_box = 0
        for i, box_item in enumerate(bboxes):
            x1, y1, x2, y2, score = box_item
            size_box = int(x2 - x1) * int(y2 - y1)
            if(size_box > max_box):
                index = i
                max_box = size_box

        aligned_face = face_align.norm_crop(img, kpss[index])
        log.ex_time_detection = round(time.time() - start_time_detect, 3)
        return status, aligned_face

    def detect_faces(self, img, log):
        start_time_detect = time.time()
        status, bboxes, kpss = self._face_detector(img)
        if status == 0:
            return status, FACE_NOT_FOUND
            
        crop_faces = []
        for i, box_item in enumerate(bboxes):
            x1, y1, x2, y2, score = box_item
            width = x2-x1
            height = y2-y1
            if width > config.MIN_SIZE_FACE and height > config.MIN_SIZE_FACE:
                aligned_face = face_align.norm_crop(img, kpss[i])
                crop_faces.append(aligned_face)
       
        log.ex_time_detection = round(time.time() - start_time_detect, 3)
        return status, crop_faces

class RandomBoundingBoxGenerator:
    def __init__(self, interval_time = 300):
        self.bounding_boxes = []
        self.last_generated_time = None
        self.interval_time = interval_time

    def generate_bounding_boxes(self):
        quadrants = [
            (0, 0, 0.5, 0.5),  # Top-left
            (0, 0.5, 0.5, 1),  # Top-right
            (0.5, 0, 1, 0.5),  # Bottom-left
            (0.5, 0.5, 1, 1)   # Bottom-right
        ]

        # Define a central exclusion zone (normalized coordinates)
        exclusion_zone = (0.1, 0.1, 0.9, 0.9)  # 20% of the center

        # Select random 2 out of 4 quadrants
        selected_quadrants = random.sample(quadrants, 2)

        self.bounding_boxes = []
        for quadrant in selected_quadrants:
            x_start, y_start, x_end, y_end = quadrant

            # Randomly generate bounding box within the quadrant (normalized coordinates)
            while True:
                box_width = random.uniform(0.07, 0.15 * (x_end - x_start))
                box_height = random.uniform(0.07, 0.15 * (y_end - y_start))
                x1 = random.uniform(x_start, x_end - box_width)
                y1 = random.uniform(y_start, y_end - box_height)
                x2 = x1 + box_width
                y2 = y1 + box_height

                # Check if the box is outside the exclusion zone
                if (x2 < exclusion_zone[0] or x1 > exclusion_zone[2] or
                        y2 < exclusion_zone[1] or y1 > exclusion_zone[3]):
                    self.bounding_boxes.append((round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)))
                    break
        self.last_generated_time = time.time()

    def get_bounding_boxes(self):
        current_time = time.time()

        # Check if more than 5 minutes have passed since the last generation
        if self.last_generated_time is None or (current_time - self.last_generated_time) > self.interval_time:
            self.generate_bounding_boxes()

        expires_in = int(self.interval_time - (current_time - self.last_generated_time))
        result = {
            "boundingboxes": self.bounding_boxes,
            "expires_in": expires_in
        }

        return result
    
class AntiSpoofClassifier:
    def __init__(self, face_detector_, model_fas_1_0_, model_fas_2_7_, model_fas_4_0_, model_fas_deepfake_):

        self.Face_Detector = face_detector_
        self.Model_FAS_1_0 = model_fas_1_0_
        self.Model_FAS_2_7 = model_fas_2_7_
        self.Model_FAS_4_0 = model_fas_4_0_
        self.Model_FAS_Deepfake = model_fas_deepfake_

        self.FAS_CONF_THRESHOLD = config.FAS_CONF_THRESHOLD
        self.FAS_CONF_THRESHOLD_SUB_MODEL = config.FAS_CONF_THRESHOLD_SUB_MODEL
        self.FAS_CONF_THRESHOLD_DEEPFAKE_MODEL = config.FAS_CONF_THRESHOLD_DEEPFAKE_MODEL


    def forward_model_silent(self, image_crop2_7, image_crop4_0):
        prediction_output = np.zeros((1, 2))
        # 1: real ; 0: spoof
        prediction = np.zeros((1, 3))
        prediction += self.Model_FAS_2_7.inference(image_crop2_7)
        # prediction += self.Model_FAS_2_7.inference(image_crop4_0)
        prediction += self.Model_FAS_4_0.inference(image_crop4_0)
        prediction_output[0][0], prediction_output[0][1] = prediction[0][1]/2, (prediction[0][0] +  prediction[0][2])/2
        
        return prediction_output[0]

    def forward_model_finetune(self, image, image_crop2_0):
        result_2 = self.Model_FAS_1_0.predict(image)
        result_2 += self.Model_FAS_1_0.predict(image_crop2_0)
        
        return result_2 / 2


    def forward(self, image):
        image_org = image
        t_start = time.time()
        image_bbox, image_kps = self.Face_Detector.predict(image_org)
        print('[DETECT] time face detect = ', time.time() - t_start)
        if image_bbox is not None:
            image_face = self.Face_Detector.crop_image_with_padding(image_org, image_bbox, image_size = 224, padding = 0.02)
            image_crop2_0 = self.Face_Detector.crop_image_with_padding(image_org, image_bbox, image_size = 224, padding = 0.5)
            image_crop2_7 = self.Face_Detector.crop_image_with_padding(image_org, image_bbox, image_size = 80, padding = 0.2)
            image_crop4_0 = self.Face_Detector.crop_image_with_padding(image_org, image_bbox, image_size = 80, padding = 0.5)
            # print(">>>>>>> Time Detect Face : ", time.time() - t_start)
            # cv2.imwrite('facecrop.jpg',image_face)e
            # foward model silent pretrained
            start_recap = time.time()
            result_1 = self.forward_model_silent(image_crop2_7, image_crop4_0)
            print('[DETECT] time recap pre = ', time.time() - start_recap)
            # foward model resnet finetune
            start_recap_finetune = time.time()
            result_2  = self.forward_model_finetune(image_face, image_crop2_0)
            print('[DETECT] time recap finetune = ', time.time() - start_recap_finetune)

            result_3 = np.array([1, 0])
            if config.USE_DEEPFAKE_MODEL == 1:
                # foward model resnet deepfake
                start_df = time.time()
                result_3  = self.Model_FAS_Deepfake.predict(image_face)
                print('[DETECT] time deepfake = ', time.time() - start_df)

            return result_1, result_2, result_3
        else:
            return None, None, None

    def predict(self, image):
        result = {
            "label": "",
            "score": 0,
            "error_code": "",
            "message": ""
        }
        result_model1, result_model2, result_model3 = self.forward(image)
        print(">>> result_model1:: ", result_model1)
        print(">>> result_model2:: ", result_model2)
        print(">>> result_model3:: ", result_model3)
        print('-------------------------------------')

        if result_model1 is None or result_model2 is None:
            result.update({
                "error_code": NO_FACE,
                "message": "The face cannot be detected"
                })
        else:
            live_score = round((result_model2[0] + result_model1[0] + result_model3[0])/3 , 2)
            if result_model2[0] > self.FAS_CONF_THRESHOLD and result_model1[0] > self.FAS_CONF_THRESHOLD_SUB_MODEL and result_model3[0] > self.FAS_CONF_THRESHOLD_DEEPFAKE_MODEL:
                result.update({
                                "label": LIVE_CLASS_NAME,
                                "score": max(live_score, 0.7)
                            })
            else:
                result.update({
                    "label": SPOOF_CLASS_NAME,
                    "score": max(1 - live_score, 0.7)
                })
        
        return result
    
class DetectSpoofVideo:
    def __init__(self, anti_spoof_classifier, face_detector):
        self.anti_spoof_classifier = anti_spoof_classifier
        self.face_detector = face_detector
        self.result_frame_status = []
        self.result_frame_score = []

        # check face area
        self.ratio_face_area_to_frame = 0.0

        # result check similarity image
        self.is_similarity_images_valid = False
        self.similarity_images_result = []

        # result check face direction
        self.result_face_direction = []
        self.is_enough_direction_face = False
        self.frontal_face_image = None
    
    def resize_image_to_640(self, image):
        w = image.shape[1]
        h = image.shape[0]
        scale = 1.0
        target_size = 640
        if w > h:
            scale = target_size/w
            w = target_size
            h = h * scale
        else:
            scale = target_size/h
            h = target_size
            w = w * scale
        image = cv2.resize(image, (int(w), int(h)))
        return image


    def check_similarity_images(self, frame_list):
        '''
            kiểm tra video được tao ra từ một ảnh tĩnh
        '''
        start_time = time.time()
        self.is_similarity_images_valid = False
        self.similarity_images_result = []

        for _ in range(config.NUMBER_CHECK_DUPLICATE):
            pair_frames = random.sample(frame_list, 2)
            if pair_frames[0].shape[0] == pair_frames[1].shape[0] and pair_frames[0].shape[1] == pair_frames[1].shape[1]:
                first_img = self.resize_image_to_640(pair_frames[0])
                second_img = self.resize_image_to_640(pair_frames[1])
                first_gray = cv2.cvtColor(first_img, cv2.COLOR_BGR2GRAY)
                second_gray = cv2.cvtColor(second_img, cv2.COLOR_BGR2GRAY)
                score, diff = structural_similarity(first_gray, second_gray, full=True)
                # print('>>> [check similarity images] score similarity = ', score)
                if score > config.THRESHOLD_DUPLICATE_IMAGE_SIMILARITY:
                    self.similarity_images_result.append(DUPLICATE_IMAGE)
                elif score < config.THRESHOLD_DIFFERENT_IMAGE_SIMILARITY:
                    self.similarity_images_result.append(DIFFERENT_IMAGE)
                else:
                    self.similarity_images_result.append(TRUE_IMAGE)
            else:
                # print('>>> [check duplicate images] invalid image size') # pragma: no cover
                self.similarity_images_result.append(INVALID_IMG_SIZE) # pragma: no cover
                break # pragma: no cover
        if INVALID_IMG_SIZE not in self.similarity_images_result and \
            len(self.similarity_images_result) == config.NUMBER_CHECK_DUPLICATE:
            
            total_frame_true_image = self.similarity_images_result.count(TRUE_IMAGE)
            if total_frame_true_image >= (0.5 * len(self.similarity_images_result)):
                self.is_similarity_images_valid = True
        print('[IMAGE DUPLICATE] time check image duplicate = ', time.time() - start_time)
    
    def calculate_angle(self, a, b, c):
        ba = a - b
        bc = c - b 
        cosine_angle = np.dot(ba, bc)/(np.linalg.norm(ba)*np.linalg.norm(bc))
        angle = np.arccos(cosine_angle)
        return np.degrees(angle)
    
    def check_face_direction(self, frame_list):
        '''
            kiểm tra hướng của khuôn mặt
        '''
        start_time = time.time()
        self.result_face_direction = []
        self.is_enough_direction_face = False
        self.frontal_face_image = None

        for frame in frame_list:
            start_time = time.time()
            _, face_kps = self.face_detector.predict(frame)
            ang_right = self.calculate_angle(face_kps[0], face_kps[1], face_kps[2])
            ang_left = self.calculate_angle(face_kps[1], face_kps[0], face_kps[2])
            if ((int(ang_right) in range(35, 57)) and (int(ang_left) in range(35, 58))):
                pred_direction = FRONTAL_DIRECTION
                self.frontal_face_image = frame
            else: 
                if ang_right < ang_left:
                    pred_direction = LEFT_DIRECTION
                else:
                    pred_direction = RIGHT_DIRECTION
            self.result_face_direction.append(pred_direction)
            # print('pred_direction = ', pred_direction)
            # print('time check direct = ', time.time() - start_time)
        
        total_frame_frontal_direction = self.result_face_direction.count(FRONTAL_DIRECTION)
        total_frame_left_direction = self.result_face_direction.count(LEFT_DIRECTION)
        total_frame_right_direction = self.result_face_direction.count(RIGHT_DIRECTION)

        if total_frame_frontal_direction > 0 and total_frame_left_direction > 0 and total_frame_right_direction > 0:
            self.is_enough_direction_face = True
        print('[FACE DIRECTION] time check direction = ', time.time() - start_time)
    
    def check_face_area(self, frame_list):
        '''
            tính tỷ lệ diện tích khuôn mặt trên khung hình
        '''
        self.ratio_face_area_to_frame = 0

        start_time = time.time()
        frame_area = frame_list[0].shape[0] * frame_list[0].shape[1]
        list_ratio_area = []
        for frame in frame_list:
            face_bboxes, _ = self.face_detector.predict(frame)
            if face_bboxes is not None:
                [x1, y1, x2, y2] = face_bboxes
                w_box = x2 - x1
                h_box = y2 - y1
                face_area = w_box * h_box
                ratio_area = face_area / frame_area
                list_ratio_area.append(ratio_area)
        # print('[FACE AREA] list_ratio_area = ', list_ratio_area)
        print('[FACE AREA] time check face area = ', time.time() - start_time)
        self.ratio_face_area_to_frame = np.mean(list_ratio_area)
        # print('FACE AREA: ',self.ratio_face_area_to_frame)
    def detect_spoofing(self, frame_list_check):
        start_time = time.time()
        for frame in frame_list_check:
            rs_check = self.anti_spoof_classifier.predict(frame)
            self.result_frame_status.append(rs_check["label"])
            self.result_frame_score.append(rs_check["score"])
        print('[DETECT SPOOFING] time detect = ', time.time() - start_time)

    def decode_video(self, video_content, frame_skip=10):
        t_start = time.time()
        frames = []
        print("Start decoding video")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(video_content)
            temp_video_path = temp_video.name

        try:
            metadata = ffmpeg.probe(temp_video_path)
        except ffmpeg.Error as e:
            print("ffprobe error:", e.stderr.decode())
            raise ValueError("Error extracting metadata from video.")

        video_capture = cv2.VideoCapture(temp_video_path)

        if not video_capture.isOpened():
            raise ValueError("Error opening video stream or file")

        frame_count = 0
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            if frame_count % frame_skip == 0:
                frames.append(frame)

            frame_count += 1

        video_capture.release()
        os.remove(temp_video_path)

        print(f"Time to extract video: {time.time() - t_start:.2f} seconds, Number of frames: {len(frames)}")
        return frames


    # def predict(self, video, timestamp, unique_device_id, x_signature, log, result, is_test, is_pose_check):
    def predict(self, video, log, result, is_pose_check):

        t_start = time.time()
        video_content = video.read()
        self.result_frame_status = []
        self.result_frame_score = []

        log.ex_time_authen_signature = time.time() - t_start

        t_start_decode = time.time()
        frames_list = self.decode_video(video_content, frame_skip=config.SKIP_FRAME)
        log.ex_time_videodecode = time.time() - t_start_decode

        # print(f"video_metadata: {video_metadata}")

        image_upload = None
        frame_upload = None

        t_start_model = time.time()
        if len(frames_list) > 1:
                frame_upload = frames_list
                print('FRAME UPLOAD: ', frame_upload[0].shape, frame_upload[1].shape)
                print("LEN UPLOAD: ", len(frame_upload))
                cv2.imwrite('img_test.jpg', frames_list[0])
                
                num_frame_check = min(config.NUM_FRAME_CHECK, len(frames_list))
                frame_list_check = random.sample(frames_list, num_frame_check)
                frame_upload = frame_list_check
                print('FRAME UPLOAD: ', frame_upload[0].shape, frame_upload[1].shape)
                print("LEN UPLOAD: ", len(frame_upload))
                
                if is_pose_check:
                    thread_check_face_direction= threading.Thread(target=self.check_face_direction, args=(frames_list,))
                    thread_check_face_direction.start()

                thread_check_face_area = threading.Thread(target=self.check_face_area, args=(frames_list,))
                thread_check_similarity_images = threading.Thread(target=self.check_similarity_images, args=(frames_list,))
                thread_detect_spooding = threading.Thread(target=self.detect_spoofing, args=(frame_list_check, ))
                thread_check_similarity_images.start()
                thread_check_face_area.start()
                thread_detect_spooding.start()

                if is_pose_check:
                    thread_check_face_direction.join()
                thread_check_similarity_images.join()
                thread_check_face_area.join()   
                thread_detect_spooding.join()

        else:
                result.update({
                    "error_code": DECODE_VIDEO_FALSE,
                    "message": "Video cannot decode to images"
                })
                return result, image_upload, frame_upload
            
        log.ex_result_frame_status = str(self.result_frame_status)
        log.ex_result_frame_score = str(self.result_frame_score)
        image_upload = self.frontal_face_image if self.frontal_face_image is not None else frames_list[0] # pragma: no cover

        if is_pose_check:
            face_area_threshold = config.FACE_AREA_THRESHOLD_POSE
        else:
            face_area_threshold = config.FACE_AREA_THRESHOLD_NO_POSE

        # print('FACE_AREA_THRESHOLD: ',face_area_threshold)
        # print('IS POSE CHECK: ',is_pose_check)
        if self.is_similarity_images_valid == False:
            result.update({
                'label': SPOOF_CLASS_NAME,
                'score': 1.0
            })
        elif self.ratio_face_area_to_frame < face_area_threshold:
            result.update({
                "error_code": FACE_TOO_FAR,
                "message": "face is too far away"
            })
        elif self.is_enough_direction_face == False and is_pose_check == 1: # pragma: no cover
            result.update({
                "error_code": NOT_ENOUGH_FACE_DIRECTION,
                "message": "not enough face direction"
            }) # pragma: no cover
        else:
            total_frame_is_live = self.result_frame_status.count(LIVE_CLASS_NAME) # pragma: no cover 
            if (total_frame_is_live / len(self.result_frame_status)) > config.VOTE_THRESHOLD: # pragma: no cover
                result.update({
                    'label': LIVE_CLASS_NAME,
                    'score': np.mean(self.result_frame_score)
                }) # pragma: no cover
            else:
                result.update({
                    'label': SPOOF_CLASS_NAME,
                    'score': np.mean(self.result_frame_score)
                }) # pragma: no cover

        log.ex_time_modelpredict = time.time() - t_start_model
        log.ex_similarity_images_result = str(self.similarity_images_result)
        log.ex_is_similarity_images_valid = 1 if self.is_similarity_images_valid else 0
        log.ex_result_face_direction = str(self.result_face_direction)
        log.ex_is_enough_face_direction = 1 if self.is_enough_direction_face == True else 0
        log.ex_ratio_face_area_to_frame = self.ratio_face_area_to_frame
        print("=" * 50)

        return result, image_upload, frame_upload