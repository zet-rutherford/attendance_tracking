import os
import cv2
import math
import torch
import numpy as np
import torch.nn.functional as F
import sys

from app.gvision.face_anti_spoof.model_lib.MiniFASNet import MiniFASNetV1, MiniFASNetV2,MiniFASNetV1SE,MiniFASNetV2SE
from app.gvision.face_anti_spoof.data_io import transform as trans
from app.gvision.face_anti_spoof.utility import get_kernel, parse_model_name


sys.path.append('./app/gvision/face_anti_spoof')
from nets.utils import get_model, load_pretrain

MODEL_MAPPING = {
    'MiniFASNetV1': MiniFASNetV1,
    'MiniFASNetV2': MiniFASNetV2,
    'MiniFASNetV1SE':MiniFASNetV1SE,
    'MiniFASNetV2SE':MiniFASNetV2SE
}

class Detection:
    def __init__(self):
        caffemodel = "./app/gvision/weights/detection_model/Widerface-RetinaFace.caffemodel"
        deploy = "./app/gvision/weights/detection_model/deploy.prototxt"
        self.detector = cv2.dnn.readNetFromCaffe(deploy, caffemodel)
        self.detector_confidence = 0.3

    def get_bbox(self, img):
        height, width = img.shape[0], img.shape[1]
        aspect_ratio = width / height
        if img.shape[1] * img.shape[0] >= 192 * 192:
            img = cv2.resize(img,
                             (int(192 * math.sqrt(aspect_ratio)),
                              int(192 / math.sqrt(aspect_ratio))), interpolation=cv2.INTER_LINEAR)

        blob = cv2.dnn.blobFromImage(img, 1, mean=(104, 117, 123))
        self.detector.setInput(blob, 'data')
        out = self.detector.forward('detection_out').squeeze()

        max_conf_index = np.argmax(out[:, 2])
        left, top, right, bottom = out[max_conf_index, 3]*width, out[max_conf_index, 4]*height, \
                                   out[max_conf_index, 5]*width, out[max_conf_index, 6]*height
        bbox = [int(left), int(top), int(right-left+1), int(bottom-top+1)]

        if out[max_conf_index][2] > self.detector_confidence:
            return bbox
        else:
            return None


class AntiSpoofPredict(Detection):
    def __init__(self, device_id):
        super(AntiSpoofPredict, self).__init__()
        self.device = torch.device("cuda:{}".format(device_id)
                                   if torch.cuda.is_available() else "cpu")
        print("INIT AntiSpoofPredict :: [DEVICE] :: ", self.device)

    def _load_model(self, model_path):
        # define model
        model_name = os.path.basename(model_path)
        h_input, w_input, model_type, _ = parse_model_name(model_name)
        self.kernel_size = get_kernel(h_input, w_input,)
        self.model = MODEL_MAPPING[model_type](conv6_kernel=self.kernel_size).to(self.device)

        # load model weight
        state_dict = torch.load(model_path, map_location=self.device)
        keys = iter(state_dict)
        first_layer_name = keys.__next__()
        if first_layer_name.find('module.') >= 0:
            from collections import OrderedDict
            new_state_dict = OrderedDict()
            for key, value in state_dict.items():
                name_key = key[7:]
                new_state_dict[name_key] = value
            self.model.load_state_dict(new_state_dict)
        else:
            self.model.load_state_dict(state_dict)
        return None

    def predict(self, img, model_path):
        test_transform = trans.Compose([
            trans.ToTensor(),
        ])
        img = test_transform(img)
        img = img.unsqueeze(0).to(self.device)
        self._load_model(model_path)
        self.model.eval()
        with torch.no_grad():
            result = self.model.forward(img)
            result = F.softmax(result, dim=1).cpu().numpy()
        return result

    def inference(self, img):
        test_transform = trans.Compose([
            trans.ToTensor(),
        ])
        img = test_transform(img)
        img = img.unsqueeze(0).to(self.device)
        self.model.eval()
        with torch.no_grad():
            result = self.model.forward(img)
            result = F.softmax(result, dim=1).cpu().numpy()
        return result

class CropImage:
    @staticmethod
    def _get_new_box(src_w, src_h, bbox, scale):
        x = bbox[0]
        y = bbox[1]
        box_w = bbox[2]
        box_h = bbox[3]

        scale = min((src_h-1)/box_h, min((src_w-1)/box_w, scale))

        new_width = box_w * scale
        new_height = box_h * scale
        center_x, center_y = box_w/2+x, box_h/2+y

        left_top_x = center_x-new_width/2
        left_top_y = center_y-new_height/2
        right_bottom_x = center_x+new_width/2
        right_bottom_y = center_y+new_height/2

        if left_top_x < 0:
            right_bottom_x -= left_top_x
            left_top_x = 0

        if left_top_y < 0:
            right_bottom_y -= left_top_y
            left_top_y = 0

        if right_bottom_x > src_w-1:
            left_top_x -= right_bottom_x-src_w+1
            right_bottom_x = src_w-1

        if right_bottom_y > src_h-1:
            left_top_y -= right_bottom_y-src_h+1
            right_bottom_y = src_h-1

        return int(left_top_x), int(left_top_y),\
               int(right_bottom_x), int(right_bottom_y)

    def crop(self, org_img, bbox, scale, out_w, out_h, crop=True):

        if not crop:
            dst_img = cv2.resize(org_img, (out_w, out_h))
        else:
            src_h, src_w, _ = np.shape(org_img)
            left_top_x, left_top_y, \
                right_bottom_x, right_bottom_y = self._get_new_box(src_w, src_h, bbox, scale)

            img = org_img[left_top_y: right_bottom_y+1,
                          left_top_x: right_bottom_x+1]
            dst_img = cv2.resize(img, (out_w, out_h))
        return dst_img


class ImageClassifier:
    def __init__(self, model_path, arch='resnet50', num_classes=2, input_size=224, device_id=0):
        self.device = f"cuda:{device_id}" if torch.cuda.is_available() else "cpu"
        print(">>>>>>   ImageClassifier ::: Device ::: ", self.device, "  ::: Model_path ::: ", model_path)

        self.input_size = input_size
        self.model = self._load_model(model_path, arch, num_classes)
        
    def _load_model(self, model_path, arch, num_classes):
        # print(f">>>>>>  ImageClassifier :: Creating model :: '{arch}'")
        model = get_model(arch, num_classes, False)
        model.cuda() if self.device.startswith("cuda") else model.cpu()
        load_pretrain(model_path, model)
        model.eval()  # Set the model to evaluation mode
        return model

    def _preprocess_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        image = cv2.resize(image, (self.input_size, self.input_size))  # Resize the image

        # Normalize the image
        image = image.astype(np.float32) / 255.0  # Normalize to [0, 1]
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        image = (image - mean) / std

        # Convert the numpy array to a tensor
        image_tensor = torch.from_numpy(image.transpose(2, 0, 1))  # Change from HWC to CHW format
        image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
        return image_tensor.type(torch.float32).to(self.device)

    def predict(self, image, threshold = 0.5):
        image_tensor = self._preprocess_image(image)

        # Perform inference
        with torch.no_grad():
            output = self.model(image_tensor)

        classification_output = output[1]

        # Apply softmax to get probabilities
        probabilities = F.softmax(classification_output, dim=1)

        return probabilities[0].cpu().numpy()



