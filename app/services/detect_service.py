import torch

from app.core.pixelseal import model
from app.services.image_service import ImageService


class DetectService:

    @staticmethod
    def detect(image_path):

        image = ImageService.load_image(image_path)

        outputs = model.detect(
            imgs=image,
            is_video=False,
        )

        preds = outputs["preds"]

        confidence = torch.sigmoid(preds[:, 0])

        bits = (preds[:, 1:] > 0).int()

        return {
            "confidence": confidence,
            "bits": bits,
        }

    @staticmethod
    def extract(image_path):

        image = ImageService.load_image(image_path)

        bits = model.extract_message(image)

        return bits.int()