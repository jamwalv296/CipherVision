import torch
import torch.nn as nn
import torch.nn.functional as F

from models.blocks import RDBWithAttention


class Encoder(nn.Module):
    def __init__(self, payload_bits: int = 2048, channels: int = 64, num_blocks: int = 4):
        super().__init__()
        self.channels = channels
        self.payload_seed_size = 16
        self.payload_fc = nn.Linear(payload_bits, channels * self.payload_seed_size * self.payload_seed_size)

        self.image_conv_in = nn.Conv2d(3, channels, 3, 1, 1)
        self.fusion_conv = nn.Conv2d(channels * 2, channels, 3, 1, 1)

        self.blocks = nn.ModuleList([RDBWithAttention(channels) for _ in range(num_blocks)])

        self.conv_out = nn.Conv2d(channels, 3, 3, 1, 1)
        self.tanh = nn.Tanh()

    def forward(self, cover_image: torch.Tensor, payload_bits: torch.Tensor) -> torch.Tensor:
        b, _, h, w = cover_image.shape

        payload_feat = self.payload_fc(payload_bits)
        payload_feat = payload_feat.view(b, self.channels, self.payload_seed_size, self.payload_seed_size)
        payload_feat = F.interpolate(payload_feat, size=(h, w), mode="nearest")

        image_feat = self.image_conv_in(cover_image)

        fused = self.fusion_conv(torch.cat([image_feat, payload_feat], dim=1))

        x = fused
        for block in self.blocks:
            x = block(x)

        residual = self.tanh(self.conv_out(x))
        stego_image = cover_image + residual

        return stego_image