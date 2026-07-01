import os
import glob
import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image

class DIV2KPayloadDataset(Dataset):
    def __init__(self, img_dir, payload_len=64, img_size=256, max_imgs=None):
        self.img_paths = sorted(glob.glob(os.path.join(img_dir, "**/*.png"), recursive=True))
        if not self.img_paths:
            self.img_paths = sorted(glob.glob(os.path.join(img_dir, "**/*.jpg"), recursive=True))
        if max_imgs:
            self.img_paths = self.img_paths[:max_imgs]
        self.payload_len = payload_len
        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor()
        ])
        torch.manual_seed(42)
        self.static_payloads = torch.randint(0, 2, (len(self.img_paths), payload_len)).float()

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img = Image.open(self.img_paths[idx]).convert('RGB')
        img_tensor = self.transform(img)
        payload = self.static_payloads[idx]
        return img_tensor, payload