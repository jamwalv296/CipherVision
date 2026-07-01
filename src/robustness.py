import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class RobustnessLayer(nn.Module):
    def __init__(self):
        super(RobustnessLayer, self).__init__()

    def add_noise(self, x, std=0.02):
        noise = torch.randn_like(x) * std
        return torch.clamp(x + noise, 0.0, 1.0)

    def gaussian_blur(self, x, kernel_size=3, sigma=1.0):
        radius = kernel_size // 2
        kernel_1d = np.arange(-radius, radius + 1, dtype=np.float32)
        kernel_1d = np.exp(-kernel_1d**2 / (2 * sigma**2))
        kernel_1d /= kernel_1d.sum()
        
        kernel_2d = np.outer(kernel_1d, kernel_1d)
        kernel_tensor = torch.from_numpy(kernel_2d).unsqueeze(0).unsqueeze(0).repeat(3, 1, 1, 1).to(x.device)
        
        return torch.clamp(F.conv2d(x, kernel_tensor, padding=radius, groups=3), 0.0, 1.0)

    def jpeg_approximation(self, x, quality=50):
        b, c, h, w = x.size()
        x_dct = torch.fft.fft2(x)
        mask = torch.ones_like(x_dct)
        cutoff = int((quality / 100.0) * (h // 2))
        mask[:, :, cutoff:, :] = 0.0
        mask[:, :, :, cutoff:] = 0.0
        return torch.clamp(torch.real(torch.fft.ifft2(x_dct * mask)), 0.0, 1.0)

    def color_jitter(self, x, brightness=0.1, contrast=0.1):
        if brightness > 0:
            b_factor = torch.empty(1, device=x.device).uniform_(-brightness, brightness)
            x = x + b_factor
        if contrast > 0:
            c_factor = torch.empty(1, device=x.device).uniform_(1.0 - contrast, 1.0 + contrast)
            x = (x - 0.5) * c_factor + 0.5
        return torch.clamp(x, 0.0, 1.0)

    def forward(self, x):
        if not self.training:
            return x
            
        attack_type = torch.randint(0, 4, (1,)).item()
        
        if attack_type == 0:
            return self.add_noise(x)
        elif attack_type == 1:
            return self.gaussian_blur(x)
        elif attack_type == 2:
            return self.jpeg_approximation(x)
        elif attack_type == 3:
            return self.color_jitter(x)
            
        return x