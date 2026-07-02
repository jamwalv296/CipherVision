import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import random


def identity(x: torch.Tensor) -> torch.Tensor:
    return x


def gaussian_noise(x: torch.Tensor, std: float = 0.02) -> torch.Tensor:
    noise = torch.randn_like(x) * std
    return x + noise


def _gaussian_kernel(kernel_size: int, sigma: float, channels: int, device):
    coords = torch.arange(kernel_size, dtype=torch.float32, device=device) - (kernel_size - 1) / 2
    g = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
    g = g / g.sum()
    kernel_2d = torch.outer(g, g)
    kernel_2d = kernel_2d.expand(channels, 1, kernel_size, kernel_size)
    return kernel_2d


def gaussian_blur(x: torch.Tensor, kernel_size: int = 5, sigma: float = 1.2) -> torch.Tensor:
    channels = x.shape[1]
    kernel = _gaussian_kernel(kernel_size, sigma, channels, x.device)
    padding = kernel_size // 2
    return F.conv2d(x, kernel, padding=padding, groups=channels)


def brightness(x: torch.Tensor, delta_range: float = 0.15) -> torch.Tensor:
    delta = (torch.rand(x.size(0), 1, 1, 1, device=x.device) * 2 - 1) * delta_range
    return x + delta


def contrast(x: torch.Tensor, factor_range: float = 0.2) -> torch.Tensor:
    factor = 1.0 + (torch.rand(x.size(0), 1, 1, 1, device=x.device) * 2 - 1) * factor_range
    mean = x.mean(dim=[1, 2, 3], keepdim=True)
    return (x - mean) * factor + mean


def color_jitter(x: torch.Tensor, jitter_range: float = 0.1) -> torch.Tensor:
    factors = 1.0 + (torch.rand(x.size(0), x.size(1), 1, 1, device=x.device) * 2 - 1) * jitter_range
    return x * factors


def resize_attack(x: torch.Tensor, scale_range=(0.5, 0.9)) -> torch.Tensor:
    b, c, h, w = x.shape
    scale = random.uniform(*scale_range)
    new_h, new_w = max(8, int(h * scale)), max(8, int(w * scale))
    down = F.interpolate(x, size=(new_h, new_w), mode="bilinear", align_corners=False)
    up = F.interpolate(down, size=(h, w), mode="bilinear", align_corners=False)
    return up


def crop_attack(x: torch.Tensor, crop_ratio_range=(0.7, 0.95)) -> torch.Tensor:
    b, c, h, w = x.shape
    ratio = random.uniform(*crop_ratio_range)
    crop_h, crop_w = int(h * ratio), int(w * ratio)
    top = random.randint(0, h - crop_h)
    left = random.randint(0, w - crop_w)
    cropped = x[:, :, top:top + crop_h, left:left + crop_w]
    resized = F.interpolate(cropped, size=(h, w), mode="bilinear", align_corners=False)
    return resized


class DifferentiableJPEG(nn.Module):
    def __init__(self, quality: float = 50.0):
        super().__init__()
        self.quality = quality
        self.register_buffer("luma_quant", self._quant_table(luma=True))
        self.register_buffer("chroma_quant", self._quant_table(luma=False))

    def _quant_table(self, luma: bool) -> torch.Tensor:
        if luma:
            base = torch.tensor([
                [16, 11, 10, 16, 24, 40, 51, 61],
                [12, 12, 14, 19, 26, 58, 60, 55],
                [14, 13, 16, 24, 40, 57, 69, 56],
                [14, 17, 22, 29, 51, 87, 80, 62],
                [18, 22, 37, 56, 68, 109, 103, 77],
                [24, 35, 55, 64, 81, 104, 113, 92],
                [49, 64, 78, 87, 103, 121, 120, 101],
                [72, 92, 95, 98, 112, 100, 103, 99],
            ], dtype=torch.float32)
        else:
            base = torch.tensor([
                [17, 18, 24, 47, 99, 99, 99, 99],
                [18, 21, 26, 66, 99, 99, 99, 99],
                [24, 26, 56, 99, 99, 99, 99, 99],
                [47, 66, 99, 99, 99, 99, 99, 99],
                [99, 99, 99, 99, 99, 99, 99, 99],
                [99, 99, 99, 99, 99, 99, 99, 99],
                [99, 99, 99, 99, 99, 99, 99, 99],
                [99, 99, 99, 99, 99, 99, 99, 99],
            ], dtype=torch.float32)
        q = self.quality
        scale = 5000.0 / q if q < 50 else 200.0 - 2 * q
        table = torch.clamp((base * scale + 50) / 100, min=1.0)
        return table

    def _dct_matrix(self, device):
        n = 8
        m = torch.zeros(n, n, device=device)
        for i in range(n):
            for j in range(n):
                if i == 0:
                    m[i, j] = 1.0 / math.sqrt(n)
                else:
                    m[i, j] = math.sqrt(2.0 / n) * math.cos((2 * j + 1) * i * math.pi / (2 * n))
        return m

    def _block_dct(self, blocks: torch.Tensor, dct_mat: torch.Tensor) -> torch.Tensor:
        return dct_mat @ blocks @ dct_mat.t()

    def _block_idct(self, blocks: torch.Tensor, dct_mat: torch.Tensor) -> torch.Tensor:
        return dct_mat.t() @ blocks @ dct_mat

    def _soft_round(self, x: torch.Tensor) -> torch.Tensor:
        return x + (torch.round(x) - x).detach()

    def _process_channel(self, channel: torch.Tensor, quant_table: torch.Tensor) -> torch.Tensor:
        b, h, w = channel.shape
        pad_h = (8 - h % 8) % 8
        pad_w = (8 - w % 8) % 8
        channel = F.pad(channel, (0, pad_w, 0, pad_h), mode="replicate")
        ph, pw = channel.shape[1], channel.shape[2]

        dct_mat = self._dct_matrix(channel.device)
        blocks = channel.unfold(1, 8, 8).unfold(2, 8, 8)
        bh, bw = blocks.shape[1], blocks.shape[2]
        blocks = blocks.contiguous().view(b, bh * bw, 8, 8)

        blocks = blocks - 128.0
        dct_blocks = self._block_dct(blocks, dct_mat)
        quant = quant_table.unsqueeze(0).unsqueeze(0)
        quantized = self._soft_round(dct_blocks / quant) * quant
        recon_blocks = self._block_idct(quantized, dct_mat) + 128.0

        recon_blocks = recon_blocks.view(b, bh, bw, 8, 8)
        recon = recon_blocks.permute(0, 1, 3, 2, 4).contiguous().view(b, ph, pw)
        recon = recon[:, :h, :w]
        return recon

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x_255 = (x + 1.0) * 127.5 if x.min() < 0 else x * 255.0
        r, g, bch = x_255[:, 0], x_255[:, 1], x_255[:, 2]

        y = 0.299 * r + 0.587 * g + 0.114 * bch
        cb = -0.168736 * r - 0.331264 * g + 0.5 * bch + 128.0
        cr = 0.5 * r - 0.418688 * g - 0.081312 * bch + 128.0

        y_out = self._process_channel(y, self.luma_quant)
        cb_out = self._process_channel(cb, self.chroma_quant)
        cr_out = self._process_channel(cr, self.chroma_quant)

        r_out = y_out + 1.402 * (cr_out - 128.0)
        g_out = y_out - 0.344136 * (cb_out - 128.0) - 0.714136 * (cr_out - 128.0)
        b_out = y_out + 1.772 * (cb_out - 128.0)

        out = torch.stack([r_out, g_out, b_out], dim=1)
        out = torch.clamp(out, 0.0, 255.0)

        if x.min() < 0:
            out = out / 127.5 - 1.0
        else:
            out = out / 255.0
        return out


class RobustnessLayer(nn.Module):
    def __init__(self, jpeg_quality: float = 50.0):
        super().__init__()
        self.jpeg = DifferentiableJPEG(jpeg_quality)
        self.attack_names = [
            "identity", "gaussian_noise", "gaussian_blur",
            "brightness", "contrast", "color_jitter",
            "resize", "crop", "jpeg",
        ]

    def forward(self, x: torch.Tensor, attack_name: str = None) -> torch.Tensor:
        if attack_name is None:
            attack_name = random.choice(self.attack_names)

        if attack_name == "identity":
            out = identity(x)
        elif attack_name == "gaussian_noise":
            out = gaussian_noise(x)
        elif attack_name == "gaussian_blur":
            out = gaussian_blur(x)
        elif attack_name == "brightness":
            out = brightness(x)
        elif attack_name == "contrast":
            out = contrast(x)
        elif attack_name == "color_jitter":
            out = color_jitter(x)
        elif attack_name == "resize":
            out = resize_attack(x)
        elif attack_name == "crop":
            out = crop_attack(x)
        elif attack_name == "jpeg":
            out = self.jpeg(x)
        else:
            raise ValueError(f"unknown attack: {attack_name}")

        return torch.clamp(out, -1.0, 1.0) if x.min() < 0 else torch.clamp(out, 0.0, 1.0)