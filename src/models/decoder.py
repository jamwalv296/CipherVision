import torch
import torch.nn as nn

from models.blocks import RDBWithAttention


class Decoder(nn.Module):
    def __init__(self, payload_bits: int = 2048, channels: int = 64, num_blocks: int = 4):
        super().__init__()
        self.image_conv_in = nn.Conv2d(3, channels, 3, 1, 1)

        self.blocks = nn.ModuleList([RDBWithAttention(channels) for _ in range(num_blocks)])

        self.pool = nn.AdaptiveAvgPool2d((16, 16))
        self.fc1 = nn.Linear(channels * 16 * 16, channels * 2)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)
        self.fc2 = nn.Linear(channels * 2, payload_bits)

    def forward(self, stego_image: torch.Tensor) -> torch.Tensor:
        x = self.image_conv_in(stego_image)

        for block in self.blocks:
            x = block(x)

        x = self.pool(x)
        x = x.view(x.size(0), -1)

        x = self.lrelu(self.fc1(x))
        logits = self.fc2(x)

        return logits