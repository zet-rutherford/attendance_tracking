import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import torch

class Face_Landmark:
    def __init__(self, model_dir: Path, device: int, image_size: int = 640, conf: float = 0.7, iou: float = 0.7) -> None:
        """
        instanciate the model.

        Parameters
        ----------
        model_dir : Path
            directory where to find the model weights.

        device : str
            the device name to run the model on.
        """
        self.model = YOLO(model_dir)
        self.image_size = image_size
        self.conf = conf
        self.iou = iou
        if device < 0:
            self.device = 'cpu'
        else:
            self.device = 'cuda:{0}'.format(device)
        
        print('>>>>>>   [YOLOv8-landmark] : DEVICE_ID = {0} - model path = {1}'.format(device, model_dir))

    def crop_image_with_padding(self, image, box, image_size, padding=0.2):
        xmin, ymin, xmax, ymax = box
        padding_percentage = padding

        # Calculate the width and height of the bounding box
        width = xmax - xmin
        height = ymax - ymin

        # Calculate the padding values
        padding_width = int(width * padding_percentage)
        padding_height = int(height * padding_percentage)

        # Add padding to the bounding box
        xmin -= padding_width
        ymin -= padding_height
        xmax += padding_width
        ymax += padding_height

        # Ensure padding is equal on all sides
        width_with_padding = xmax - xmin
        height_with_padding = ymax - ymin

        if width_with_padding > height_with_padding:
            diff = width_with_padding - height_with_padding
            ymin -= diff // 2
            ymax += diff // 2
        else:
            diff = height_with_padding - width_with_padding
            xmin -= diff // 2
            xmax += diff // 2

        # Ensure that the bounding box coordinates are within the image boundaries
        xmin = max(0, xmin)
        ymin = max(0, ymin)
        xmax = min(image.shape[1], xmax)
        ymax = min(image.shape[0], ymax)

        # Recalculate width and height to ensure the box is still square within image bounds
        width = xmax - xmin
        height = ymax - ymin

        # If the adjusted box goes out of bounds, re-adjust to keep it square
        if width > height:
            ymax = ymin + width
            if ymax > image.shape[0]:
                ymax = image.shape[0]
                ymin = ymax - width
        else:
            xmax = xmin + height
            if xmax > image.shape[1]:
                xmax = image.shape[1]
                xmin = xmax - height

        # Ensure final box is within image boundaries
        xmin = max(0, xmin)
        ymin = max(0, ymin)
        xmax = min(image.shape[1], xmax)
        ymax = min(image.shape[0], ymax)

        # Crop the image with square padding
        cropped_image = image[ymin:ymax, xmin:xmax].copy()

        cropped_image = cv2.resize(cropped_image, (image_size, image_size))

        return cropped_image

    def predict(self, input_image):# pragma: no cover
        """
        Get the predictions of a model on an input image.

        Args:
            model (YOLO): The trained YOLO model.
            input_image (Image): The image on which the model will make predictions.

        Returns:
            pd.DataFrame: A DataFrame containing the predictions.
        """
        try:
            # Make predictions
            predictions = self.model.predict(
                                imgsz=self.image_size,
                                source=input_image,
                                conf=self.conf,
                                iou=self.iou,
                                device=self.device,
                                verbose=False
                                )        
            keypoints = predictions[0].to("cpu").numpy().keypoints.xy
            list_boxes = []
            list_kps = []
            
            for i, box in enumerate(predictions[0].boxes):
                box_xyxy = [int(num) for num in box.xyxy[0]]
                width_box = box_xyxy[2] - box_xyxy[0]
                height_box = box_xyxy[3] - box_xyxy[1]
                box_xyxy = [box_xyxy[0], max(0, int(box_xyxy[1] - 0.13 * height_box )), box_xyxy[2], max(0, int(box_xyxy[3] - 0.0 * height_box))]

                list_kps.append(keypoints[i])
                list_boxes.append(box_xyxy)
            if len(list_boxes) > 0:
                return list_boxes[0], list_kps[0]
            else:
                return None, None
        except:
            print(">>>>>> Predict Error .....")
            return None, None

    def _get_new_box(src_w, src_h, bbox, scale):
        x = bbox[0]
        y = bbox[1]
        box_w = bbox[2] - bbox[0]
        box_h = bbox[3] - bbox[1]

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
    


# def npAngle(a, b, c):
#     ba = a - b
#     bc = c - b 
#     cosine_angle = np.dot(ba, bc)/(np.linalg.norm(ba)*np.linalg.norm(bc))
#     angle = np.arccos(cosine_angle)
#     return np.degrees(angle)

# Face_detect = Face_Landmark(model_dir="/media/thainq97/DATA/GHTK/PROJECT/face-anti-spoofing/app/gvision/weights/detection_model/240904_face_landmark_640.pt",
#                         device = 0)
# image = cv2.imread("/home/thainq97/Pictures/photo_2_2024-09-19_14-00-54.jpg")
# face_bbox, face_kps = Face_detect.predict(image)
# print(face_bbox)
# print(face_kps)
# angR = npAngle(face_kps[0], face_kps[1], face_kps[2])
# angL = npAngle(face_kps[1], face_kps[0], face_kps[2])
# if ((int(angR) in range(35, 57)) and (int(angL) in range(35, 58))):
#     predLabel='Frontal'
# else: 
#     if angR < angL:
#         predLabel='Left Profile'
#     else:
#         predLabel='Right Profile'
# print(predLabel)