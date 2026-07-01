import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels)
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(x + self.block(x))


class Encoder(nn.Module):
    def __init__(self, payload_len=64):
        super().__init__()

        self.payload_fc = nn.Sequential(
            nn.Linear(payload_len, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, 3 * 256 * 256)
        )

        self.input = nn.Sequential(
            nn.Conv2d(6, 64, 7, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )

        self.res1 = ResidualBlock(64)
        self.res2 = ResidualBlock(64)
        self.res3 = ResidualBlock(64)
        self.res4 = ResidualBlock(64)

        self.output = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 3, 3, padding=1)
        )

    def forward(self, img, payload):
        p = self.payload_fc(payload).view(-1, 3, 256, 256)

        x = torch.cat([img, p], dim=1)

        x = self.input(x)

        x = self.res1(x)
        x = self.res2(x)
        x = self.res3(x)
        x = self.res4(x)

        residual = self.output(x)

        stego = torch.clamp(img + 0.05 * residual, 0.0, 1.0)

        return stego


class Decoder(nn.Module):
    def __init__(self, payload_len=64):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            ResidualBlock(64),
            ResidualBlock(64),
            ResidualBlock(64),
            ResidualBlock(64)
        )

        self.pool = nn.AdaptiveAvgPool2d((8, 8))

        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 8 * 8, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(1024, payload_len),
            nn.Sigmoid()
        )

    def forward(self, stego):
        x = self.features(stego)
        x = self.pool(x)
        return self.head(x)


class CipherVision(nn.Module):
    def __init__(self, payload_len=64):
        super().__init__()
        self.encoder = Encoder(payload_len)
        self.decoder = Decoder(payload_len)

    def forward(self, img, payload):
        stego = self.encoder(img, payload)
        recovered = self.decoder(stego)
        return stego, recovered