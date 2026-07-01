import torch
import torch.nn as nn
import lpips

class CipherVisionLoss(nn.Module):
    def __init__(self, mse_weight=1.0, lpips_weight=1.0, bce_weight=10.0, device='cpu'):
        super(CipherVisionLoss, self).__init__()
        self.mse_weight = mse_weight
        self.lpips_weight = lpips_weight
        self.bce_weight = bce_weight
        self.mse_loss = nn.MSELoss()
        self.bce_loss = nn.BCELoss()
        self.lpips_loss = lpips.LPIPS(net='vgg').to(device)

    def forward(self, cover_img, stego_img, original_payload, recovered_payload):
        loss_mse = self.mse_loss(stego_img, cover_img)
        
        cover_lpips = cover_img * 2.0 - 1.0
        stego_lpips = stego_img * 2.0 - 1.0
        loss_lpips = self.lpips_loss(stego_lpips, cover_lpips).mean()
        
        loss_image = (self.mse_weight * loss_mse) + (self.lpips_weight * loss_lpips)
        loss_payload = self.bce_loss(recovered_payload, original_payload)
        
        total_loss = loss_image + (self.bce_weight * loss_payload)
        
        return total_loss, loss_image, loss_payload, loss_mse, loss_lpips