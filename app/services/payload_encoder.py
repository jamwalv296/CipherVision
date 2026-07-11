import bchlib
import torch


class PayloadEncoder:

    def __init__(self):

        self.bch = bchlib.BCH(t=8, m=7)

    def encode(self, identifier: int):

        data = bytearray(identifier.to_bytes(8, "big"))

        ecc = self.bch.encode(data)

        packet = data + ecc

        bits = []

        for byte in packet:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)

        payload = torch.zeros((1, 256), dtype=torch.int64)

        payload[0, :len(bits)] = torch.tensor(bits)

        return payload