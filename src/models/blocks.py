import torch
import torch.nn as nn


class ResidualDenseBlock(nn.Module):
    def __init__(self, channels: int, growth_channels: int = 32):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, growth_channels, 3, 1, 1)
        self.conv2 = nn.Conv2d(channels + growth_channels, growth_channels, 3, 1, 1)
        self.conv3 = nn.Conv2d(channels + 2 * growth_channels, growth_channels, 3, 1, 1)
        self.conv4 = nn.Conv2d(channels + 3 * growth_channels, growth_channels, 3, 1, 1)
        self.conv5 = nn.Conv2d(channels + 4 * growth_channels, channels, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat([x, x1], dim=1)))
        x3 = self.lrelu(self.conv3(torch.cat([x, x1, x2], dim=1)))
        x4 = self.lrelu(self.conv4(torch.cat([x, x1, x2, x3], dim=1)))
        x5 = self.conv5(torch.cat([x, x1, x2, x3, x4], dim=1))
        return x + x5 * 0.2


class SpatialAttention(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels // 8, 1)
        self.conv2 = nn.Conv2d(channels // 8, channels, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        attn = torch.relu(self.conv1(x))
        attn = self.sigmoid(self.conv2(attn))
        return x * attn


class RDBWithAttention(nn.Module):
    def __init__(self, channels: int, growth_channels: int = 32):
        super().__init__()
        self.rdb = ResidualDenseBlock(channels, growth_channels)
        self.attn = SpatialAttention(channels)

    def forward(self, x):
        x = self.rdb(x)
        x = self.attn(x)
        return x