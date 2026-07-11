import bchlib


class PayloadDecoder:

    def __init__(self):

        self.bch = bchlib.BCH(t=8, m=7)

    def decode(self, bits):

        bits = bits.squeeze().tolist()

        packet = bytearray()

        for i in range(0, 120, 8):

            value = 0

            for j in range(8):

                value |= bits[i + j] << (7 - j)

            packet.append(value)

        data = bytearray(packet[:8])

        recv_ecc = bytearray(packet[8:])

        nerr = self.bch.decode(
            data=data,
            recv_ecc=recv_ecc,
        )

        if nerr < 0:
            return None

        self.bch.correct(
            data=data,
            ecc=recv_ecc,
        )

        return int.from_bytes(data, "big")