import torch
import torch.nn as nn

class Encoder(nn.Module):
    def __init__(self, payload_len=64):
        super(Encoder, self).__init__()
        self.fc = nn.Linear(payload_len, 3 * 256 * 256)
        self.conv1 = nn.Conv2d(6, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 3, kernel_size=3, padding=1)
        self.relu = nn.ReLU()

    def forward(self, img, payload):
        p_out = self.fc(payload).view(-1, 3, 256, 256)
        x = torch.cat([img, p_out], dim=1)
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        stego = torch.tanh(self.conv3(x))
        return stego

class Decoder(nn.Module):
    def __init__(self, payload_len=64):
        super(Decoder, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool2d((8, 8))
        self.fc = nn.Linear(64 * 8 * 8, payload_len)
        self.relu = nn.ReLU()

    def forward(self, stego):
        x = self.relu(self.conv1(stego))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pool(x).view(x.size(0), -1)
        payload = torch.sigmoid(self.fc(x))
        return payload

class CipherVision(nn.Module):
    def __init__(self, payload_len=64):
        super(CipherVision, self).__init__()
        self.encoder = Encoder(payload_len)
        self.decoder = Decoder(payload_len)

    def forward(self, img, payload):
        stego = self.encoder(img, payload)
        recovered_payload = self.decoder(stego)
        return stego, recovered_payload