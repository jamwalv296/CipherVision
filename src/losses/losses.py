import torch
import torch.nn as nn
import lpips


class CipherVisionLoss(nn.Module):
    def __init__(self, lambda_mse: float = 1.0, lambda_lpips: float = 0.5, lambda_bce: float = 1.0):
        super().__init__()
        self.lambda_mse = lambda_mse
        self.lambda_lpips = lambda_lpips
        self.lambda_bce = lambda_bce

        self.mse = nn.MSELoss()
        self.lpips_fn = lpips.LPIPS(net="alex")
        for param in self.lpips_fn.parameters():
            param.requires_grad = False
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, cover_image: torch.Tensor, stego_image: torch.Tensor,
                payload_bits: torch.Tensor, recovered_logits: torch.Tensor):
        mse_loss = self.mse(stego_image, cover_image)
        lpips_loss = self.lpips_fn(stego_image, cover_image).mean()
        bce_loss = self.bce(recovered_logits, payload_bits)

        total_loss = (
            self.lambda_mse * mse_loss
            + self.lambda_lpips * lpips_loss
            + self.lambda_bce * bce_loss
        )

        loss_dict = {
            "total_loss": total_loss.item(),
            "mse_loss": mse_loss.item(),
            "lpips_loss": lpips_loss.item(),
            "bce_loss": bce_loss.item(),
        }

        return total_loss, loss_dict