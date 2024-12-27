#thanks to link:https://bbs.huaweicloud.com/blogs/180532
#http://github.com/deepinsight/insightface
# -*- coding: utf-8 -*-
import cv2
import torch
import numpy as np
import onnx
import onnxruntime


class FeatureExtractor:
    def __init__(self, model_path='webface600_r50.onnx', useGpu=False, index_gpu=-1):
        # load model
        self.onnx_model = onnx.load(model_path)
        # check model
        onnx.checker.check_model(self.onnx_model)
        # create an inference

        if useGpu:
            providers = [
                ('CUDAExecutionProvider', {
                    'device_id': index_gpu,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'gpu_mem_limit': 4 * 1024 * 1024 * 1024,
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }),
                'CPUExecutionProvider',
            ]
        else:
            providers = [
                'CPUExecutionProvider',
            ]

        self.ort_session = onnxruntime.InferenceSession(model_path, providers=providers)
        self.useGPU = useGpu
        print('>>>> INIT FEATURE EXTRACTION MODEL - use_gpu={0}'.format(useGpu))

    # image to tensor
    def img2tensor(self, img):
        img  = cv2.cvtColor(img , cv2.COLOR_BGR2RGB)
        img = np.transpose(img, (2, 0, 1))
        if self.useGPU:
            img = torch.from_numpy(img).unsqueeze(0).float().cuda()
        else:
            img = torch.from_numpy(img).unsqueeze(0).float().cpu()
        img.div_(255).sub_(0.5).div_(0.5)
        return img

    def to_numpy(self, tensor):
        return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

    def __call__(self, img):
        img = cv2.resize(img, (112, 112))
        img = self.img2tensor(img)
        ort_inputs = {self.ort_session.get_inputs()[0].name: self.to_numpy(img)}
        feature = self.ort_session.run(None, ort_inputs)[0] # array
        return feature / np.linalg.norm(feature)