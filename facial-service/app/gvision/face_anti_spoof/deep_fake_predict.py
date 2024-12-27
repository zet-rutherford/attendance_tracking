import cv2 
import torch 
from nets.gen_ed import  GenResnetED
from collections import OrderedDict
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import time

class DFClassifier:
    def __init__(self, model_path, input_size, device_id):
        self.model_path  = model_path
        self.device = f"cuda:{device_id}" if torch.cuda.is_available() else "cpu"
        print(">>>>>>   DFClassifier ::: Device ::: ", self.device, " ::: Model_path ::: ", model_path)

        self.model = self.load_network()
        self.trans =  transforms.Compose([
                    transforms.Resize((input_size, input_size)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                    ])
                    
    def load_network(self):
        model = GenResnetED(pretrained=False, num_classes=1).to(self.device) 
        state_dict = torch.load(self.model_path, map_location = self.device)
        new_state_dict = OrderedDict()
        for key, value in state_dict.items():
            name_key = key.replace('module.', '', 1)
            new_state_dict[name_key] = value
        model.load_state_dict(new_state_dict, strict=True)
        model.eval()
        return model

    def predict(self, image):
        image = Image.fromarray(image)
        image = self.trans(image)
        with torch.no_grad():
            image = image.unsqueeze(0)
            image = image.to(self.device)
            score = torch.sigmoid(self.model(image)).cpu().item()
        return np.array([1 - score, score])

