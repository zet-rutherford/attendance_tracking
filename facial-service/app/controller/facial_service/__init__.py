import torch
import sys
import time
from app.extensions import config

AntiSpoofClassify = None

def getFaceDetector():
    from app.gvision.face_detection.yolov8 import Face_Landmark

    return Face_Landmark(model_dir = config.FACE_DETECTION_MODELPATH,
                        device = config.FACE_DETECTION_INDEX_GPU,
                        image_size = config.FACE_DETECTION_IMAGESIZE,
                        conf = config.FACE_DETECTION_CONF,
                        iou = config.FACE_DETECTION_IOU
                        )

def getAntiSpoofClassifierSilent():
    from app.gvision.face_anti_spoof.anti_spoof_predict import AntiSpoofPredict

    model_fas_2_7 = AntiSpoofPredict(config.FAS_INDEX_GPU)
    model_fas_2_7._load_model(config.FAS_MODEL_PATH_2_7)

    model_fas_4_0 = AntiSpoofPredict(config.FAS_INDEX_GPU)
    model_fas_4_0._load_model(config.FAS_MODEL_PATH_4_0)

    return model_fas_2_7, model_fas_4_0

def getAntiSpoofClassifierFinetune():
    from app.gvision.face_anti_spoof.anti_spoof_predict import ImageClassifier
    return ImageClassifier(model_path = config.FAS_MODEL_PATH_1_0,
                        arch = "resnet50",
                        num_classes = 2,
                        input_size = 224,
                        device_id  = config.FAS_INDEX_GPU)

def getAntiSpoofClassifierDeepfake():
    # from app.gvision.face_anti_spoof.deep_fake_predict import DFClassifier
    # return DFClassifier(model_path = config.FAS_MODEL_PATH_DEEP_FAKE,
    #                     input_size = 256,
    #                     device_id  = config.FAS_INDEX_GPU)

    from app.gvision.face_anti_spoof.anti_spoof_predict import ImageClassifier
    return ImageClassifier(model_path = config.FAS_MODEL_PATH_DEEP_FAKE,
                        arch = "resnet50",
                        num_classes = 2,
                        input_size = 224,
                        device_id  = config.FAS_INDEX_GPU)


def gen_algorithm_boxgenerator():
    from app.controller.facial_service.algorithm import RandomBoundingBoxGenerator
    return RandomBoundingBoxGenerator()

def get_algorithm_spoofing():
    from app.controller.facial_service.algorithm import AntiSpoofClassifier
    global AntiSpoofClassify
    if AntiSpoofClassify is None:
        with torch.no_grad():
            FaceDetector = getFaceDetector()
            # model Silent
            AntiSpoofClassifierSilent_2_7, AntiSpoofClassifierSilent_4_0  = getAntiSpoofClassifierSilent()
            # model finetune
            AntiSpoofClassifierFinetune = getAntiSpoofClassifierFinetune()
            # model check deepfake
            AntiSpoofClassifierDeepfake = getAntiSpoofClassifierDeepfake()
            AntiSpoofClassify = AntiSpoofClassifier(FaceDetector, AntiSpoofClassifierFinetune, AntiSpoofClassifierSilent_2_7, AntiSpoofClassifierSilent_4_0, AntiSpoofClassifierDeepfake)
            print("------------------------------LOAD ALL MODELS SUCCESS------------------------------------")
    return AntiSpoofClassify


def get_algorithm_spoofing_video():
    from app.controller.facial_service.algorithm import DetectSpoofVideo
    import cv2
    global AntiSpoofClassify
    if AntiSpoofClassify is None:
        with torch.no_grad():
            AntiSpoofClassifier = get_algorithm_spoofing()
    FaceDetector = getFaceDetector()
    
    # Warm up
    print("Warm up ......")
    image_warmup = cv2.imread("./samples/image_F1.jpg")
    for i in range(3):
        AntiSpoofClassify.predict(image_warmup)
    time.sleep(3)

    print("------------------------------LOAD ALL MODELS SUCCESS------------------------------------")
    return DetectSpoofVideo(AntiSpoofClassify, FaceDetector)

def get_feature_extractor_w600k():
    from app.gvision.feature_extraction.face_feature_extractor import FeatureExtractor
    return FeatureExtractor(model_path=config.FEATURE_EXTRACTION_MODEL_PATH, useGpu=config.USE_GPU, index_gpu=int(config.DEVICE_GPU))

def get_face_detector_scrfd():
    from app.gvision.face_detection.scrfd import FaceDetector
    return FaceDetector(model_path=config.FACE_DETECTION_MODEL_PATH, threshold=config.FACE_DETECTION_CONF_THRES,
                        useGpu=config.USE_GPU, index_gpu=config.DEVICE_GPU)


def get_algorithm():
    from app.controller.facial_service.algorithm import FaceRecognition
    with torch.no_grad():
        feature_extractor = get_feature_extractor_w600k()
        face_detector = get_face_detector_scrfd()
    return FaceRecognition(feature_extractor, face_detector)