from pathlib import Path

import torch
from videoseal.utils.cfg import setup_model_from_checkpoint


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

ROOT = Path(__file__).resolve().parents[2]

CHECKPOINT = ROOT / "checkpoints" / "pixelseal_checkpoint.pth"


class PixelSeal:

    _model = None

    @classmethod
    def get_model(cls):

        if cls._model is None:

            cls._model = setup_model_from_checkpoint(str(CHECKPOINT))
            cls._model.eval()
            cls._model.to(DEVICE)

        return cls._model


model = PixelSeal.get_model()