import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class CertificateAuthority:
    def __init__(self, key=None):
        self.key = key if key else get_random_bytes(32)

    def encrypt_metadata(self, metadata: dict) -> bytes:
        data_str = json.dumps(metadata).encode('utf-8')
        cipher = AES.new(self.key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data_str)
        return cipher.nonce + tag + ciphertext

    def decrypt_metadata(self, encrypted_bytes: bytes) -> dict:
        nonce = encrypted_bytes[:16]
        tag = encrypted_bytes[16:32]
        ciphertext = encrypted_bytes[32:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
        return json.loads(decrypted_data.decode('utf-8'))

    @staticmethod
    def bytes_to_bits(data_bytes: bytes, target_len: int = 64) -> list:
        bits = []
        for b in data_bytes:
            for i in range(8):
                bits.append((b >> (7 - i)) & 1)
        if len(bits) > target_len:
            return bits[:target_len]
        return bits + [0] * (target_len - len(bits))

    @staticmethod
    def bits_to_bytes(bits: list) -> bytes:
        data_bytes = bytearray()
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            if len(byte_bits) < 8:
                byte_bits = byte_bits + [0] * (8 - len(byte_bits))
            byte_val = 0
            for bit in byte_bits:
                byte_val = (byte_val << 1) | int(bit)
            data_bytes.append(byte_val)
        return bytes(data_bytes)