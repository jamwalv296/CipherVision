import os
import glob
import torch
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
import torchvision.transforms as T

PAYLOAD_BITS = 256

class DIV2KDataset(Dataset):
    def __init__(self, root, img_size=256, train=True):
        pattern = os.path.join(root, "*.png")
        self.files = sorted(glob.glob(pattern))
        if len(self.files) == 0:
            pattern = os.path.join(root, "*.jpg")
            self.files = sorted(glob.glob(pattern))
        if len(self.files) == 0:
            raise RuntimeError(f"No images found in {root}")
        if train:
            self.transform = T.Compose([
                T.RandomCrop(img_size, pad_if_needed=True),
                T.RandomHorizontalFlip(),
                T.ToTensor(),
                T.Normalize([0.5] * 3, [0.5] * 3),
            ])
        else:
            self.transform = T.Compose([
                T.CenterCrop(img_size),
                T.ToTensor(),
                T.Normalize([0.5] * 3, [0.5] * 3),
            ])

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        img = Image.open(self.files[idx]).convert("RGB")
        img = self.transform(img)
        payload = torch.randint(0, 2, (PAYLOAD_BITS,)).float()
        return img, payload
