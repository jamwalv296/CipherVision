from pathlib import Path

import numpy as np
import torch
from PIL import Image


class ImageService:

    @staticmethod
    def load_image(path):

        image = Image.open(path).convert("RGB")

        image = np.asarray(image).astype(np.float32) / 255.0

        image = torch.from_numpy(image)

        image = image.permute(2, 0, 1)

        image = image.unsqueeze(0)

        return image

    @staticmethod
    def save_image(tensor, path):

        tensor = tensor.squeeze(0)

        tensor = tensor.permute(1, 2, 0)

        tensor = tensor.clamp(0, 1)

        image = (tensor.numpy() * 255).astype(np.uint8)

        Image.fromarray(image).save(path)