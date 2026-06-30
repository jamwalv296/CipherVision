import torch
import torch.nn as nn
import torch.nn.functional as F

PAYLOAD_BITS = 256
IMG_SIZE = 256

class ConvBNRelu(nn.Module):
    def __init__(self, cin, cout, k=3, s=1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(cin, cout, k, s, k // 2),
            nn.BatchNorm2d(cout),
            nn.LeakyReLU(0.2, inplace=True),
        )

    def forward(self, x):
        return self.block(x)

class Encoder(nn.Module):
    def __init__(self, payload_bits=PAYLOAD_BITS, img_size=IMG_SIZE):
        super().__init__()
        self.img_size = img_size
        self.payload_fc = nn.Linear(payload_bits, img_size * img_size)
        self.conv_in = ConvBNRelu(4, 32)
        self.down1 = ConvBNRelu(32, 64, s=2)
        self.down2 = ConvBNRelu(64, 128, s=2)
        self.mid = nn.Sequential(
            ConvBNRelu(128, 128),
            ConvBNRelu(128, 128),
        )
        self.up2 = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="nearest"),
            ConvBNRelu(128, 64),
        )
        self.up1 = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="nearest"),
            ConvBNRelu(64, 32),
        )
        self.conv_out = nn.Conv2d(32, 3, 1)

    def forward(self, image, payload):
        b = image.size(0)
        p = self.payload_fc(payload).view(b, 1, self.img_size, self.img_size)
        x = torch.cat([image, p], dim=1)
        x = self.conv_in(x)
        d1 = self.down1(x)
        d2 = self.down2(d1)
        m = self.mid(d2)
        u2 = self.up2(m + d2)
        u1 = self.up1(u2 + d1)
        residual = torch.tanh(self.conv_out(u1))
        stego = image + residual * 0.05
        return torch.clamp(stego, -1, 1), residual

class Decoder(nn.Module):
    def __init__(self, payload_bits=PAYLOAD_BITS, img_size=IMG_SIZE):
        super().__init__()
        self.net = nn.Sequential(
            ConvBNRelu(3, 32, s=2),
            ConvBNRelu(32, 64, s=2),
            ConvBNRelu(64, 128, s=2),
            ConvBNRelu(128, 128, s=2),
            ConvBNRelu(128, 128, s=2),
        )
        reduced = img_size // 32
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * reduced * reduced, 512),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(512, payload_bits),
        )

    def forward(self, stego):
        x = self.net(stego)
        return self.fc(x)

class NoiseLayer(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, stego, cover):
        b = stego.size(0)
        out = stego
        if self.training:
            mode = torch.randint(0, 5, (1,)).item()
            if mode == 0:
                noise = torch.randn_like(out) * 0.02
                out = out + noise
            elif mode == 1:
                q = 8.0
                out = torch.round((out + 1) * 127.5 / q) * q / 127.5 - 1
            elif mode == 2:
                k = 3
                out = F.avg_pool2d(out, k, stride=1, padding=k // 2)
            elif mode == 3:
                scale = 0.8
                size = out.shape[-1]
                small = F.interpolate(out, scale_factor=scale, mode="bilinear", align_corners=False)
                out = F.interpolate(small, size=(size, size), mode="bilinear", align_corners=False)
            out = torch.clamp(out, -1, 1)
        return out

class CipherVisionModel(nn.Module):
    def __init__(self, payload_bits=PAYLOAD_BITS, img_size=IMG_SIZE):
        super().__init__()
        self.encoder = Encoder(payload_bits, img_size)
        self.decoder = Decoder(payload_bits, img_size)
        self.noise = NoiseLayer()

    def forward(self, image, payload):
        stego, residual = self.encoder(image, payload)
        noised = self.noise(stego, image)
        recovered = self.decoder(noised)
        return stego, residual, recovered
