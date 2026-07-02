import os
import random
import uuid

import torch
from torch.utils.data import Dataset
from PIL import Image
import torchvision.transforms as T

from crypto.certificate import create_certificate
from crypto.aes_cipher import generate_key, encrypt_certificate, bytes_to_bits


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}


class CipherVisionDataset(Dataset):
    def __init__(self, image_dir: str, patch_size: int = 256, overfit_mode: bool = False):
        self.image_dir = image_dir
        self.patch_size = patch_size
        self.overfit_mode = overfit_mode
        self.image_paths = [
            os.path.join(image_dir, f)
            for f in sorted(os.listdir(image_dir))
            if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
        ]
        if len(self.image_paths) == 0:
            raise ValueError(f"no images found in {image_dir}")

        self.random_crop = T.RandomCrop(patch_size)
        self.to_tensor = T.ToTensor()

        self.static_payloads = {}
        if self.overfit_mode:
            print("--- CipherVisionDataset initialized in OVERFIT MODE (Static Payloads) ---")
            for idx, path in enumerate(self.image_paths):
                img = self._load_image(path)
                temp_patch = img.crop((0, 0, self.patch_size, self.patch_size))
                self.static_payloads[idx] = self._generate_payload_bits(temp_patch.tobytes())

    def __len__(self):
        return len(self.image_paths)

    def _load_image(self, path: str) -> Image.Image:
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if w < self.patch_size or h < self.patch_size:
            scale = self.patch_size / min(w, h)
            new_w, new_h = int(w * scale) + 1, int(h * scale) + 1
            img = img.resize((new_w, new_h), Image.BICUBIC)
        return img

    def _generate_payload_bits(self, image_bytes: bytes) -> torch.Tensor:
        artist_id = uuid.uuid4().hex[:16]
        artwork_id = uuid.uuid4().hex[:16]
        license_code = random.choice(["CC-BY", "CC0", "ALLRIGHT", "CC-BY-SA"])

        certificate = create_certificate(artist_id, artwork_id, license_code, image_bytes)
        key = generate_key()
        payload = encrypt_certificate(key, certificate)
        bits = bytes_to_bits(payload)

        return torch.tensor(bits, dtype=torch.float32)

    def __getitem__(self, idx: int):
        path = self.image_paths[idx]
        img = self._load_image(path)
        img = self.random_crop(img)

        tensor = self.to_tensor(img)
        tensor = tensor * 2.0 - 1.0

        if self.overfit_mode:
            payload_bits = self.static_payloads[idx]
        else:
            payload_bits = self._generate_payload_bits(img.tobytes())

        return tensor, payload_bits