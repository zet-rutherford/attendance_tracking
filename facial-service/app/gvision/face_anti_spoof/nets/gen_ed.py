import torch.nn as nn
import timm
import torch
from torch.nn import functional as F


class Encoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(    
            nn.Conv2d(3, 16, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2), padding=0),

            nn.Conv2d(16, 32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2), padding=0),

            nn.Conv2d(32, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2), padding=0),

            nn.Conv2d(64, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2)),

            nn.Conv2d(128, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2), padding=0)
        )

    def forward(self, x):
        return self.features(x)

class Decoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(
            nn.ConvTranspose2d(256, 128, kernel_size=(2, 2), stride=(2, 2)),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(128, 64, kernel_size=(2, 2), stride=(2, 2)),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(64, 32, kernel_size=(2, 2), stride=(2, 2)),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(32, 16, kernel_size=(2, 2), stride=(2, 2)),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(16, 3, kernel_size=(2, 2), stride=(2, 2)),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.features(x)

class GenConViTED(nn.Module):
    def __init__(self, pretrained = True, num_classes = 1):
        super(GenConViTED, self).__init__()
        self.encoder = Encoder()
        self.decoder = Decoder()
        self.backbone = timm.create_model('convnext_tiny', pretrained=pretrained)

        self.num_features =  self.backbone.head.fc.out_features * 2
        self.fc = nn.Linear(self.num_features, self.num_features//4)
        self.fc2 = nn.Linear(self.num_features//4, num_classes)
        self.relu = nn.ReLU()

    def forward(self, images):

        encimg = self.encoder(images)
        decimg = self.decoder(encimg)

        x1 = self.backbone(decimg)
        x2 = self.backbone(images)

        x = torch.cat([x1, x2], dim=1)

        x = self.fc2(self.relu(self.fc(self.relu(x))))

        return x
    
class GenResnetED(nn.Module):
    def __init__(self, pretrained = True, num_classes = 1):
        super(GenResnetED, self).__init__()
        self.backbone = timm.create_model('resnet18', pretrained=pretrained)
        self.backbone = nn.Sequential(*(list(self.backbone.children())[:-2]))

        self.head = nn.Sequential(nn.AdaptiveAvgPool2d(1),
                                          nn.Flatten(),
                                          nn.Linear(512, num_classes))
    # def interpolate(self, img, factor):
    #     return F.interpolate(F.interpolate(img, scale_factor=factor, mode='nearest', recompute_scale_factor=True), scale_factor=1/factor, mode='nearest', recompute_scale_factor=True)
  
    def forward(self, images):
        
        # NPR  = images - self.interpolate(images, 0.5)
        # x = self.backbone(NPR*2.0/3.0)
        x = self.backbone(images)
        x = self.head(x)

        return x
    
class GenConvnextED(nn.Module):
    def __init__(self, pretrained = True, num_classes = 1):
        super(GenConvnextED, self).__init__()
        # self.encoder = Encoder()
        # self.decoder = Decoder()
        # self.backbone = resnet18(pretrained = pretrained, num_classes = num_classes)
        self.backbone = timm.create_model('convnext_tiny', pretrained=pretrained)
        self.backbone = nn.Sequential(*(list(self.backbone.children())[:-2]))

        self.head = nn.Sequential(nn.AdaptiveAvgPool2d(1),
                                          nn.Flatten(),
                                          nn.Linear(768, num_classes))
        
        # self.num_features = 128 * 2
        # self.fc = nn.Linear(self.num_features, self.num_features//4)
        # self.fc2 = nn.Linear(self.num_features//4, num_classes)
        # self.relu = nn.GELU()

    def forward(self, images):

        # encimg = self.encoder(images)
        # decimg = self.decoder(encimg)

        # x1 = self.backbone(decimg)
        # x2 = self.backbone(images)

        # x = torch.cat([x1, x2], dim=1)

        x = self.backbone(images)
        x = self.head(x)
        # x = self.fc2(self.relu(self.fc(self.relu(x))))

        return x