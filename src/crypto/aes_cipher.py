import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


NONCE_LEN = 12
TAG_LEN = 16
PAYLOAD_BYTES = 256
PAYLOAD_BITS = PAYLOAD_BYTES * 8


def generate_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)


def encrypt_certificate(key: bytes, certificate: bytes) -> bytes:
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_LEN)
    ciphertext_with_tag = aesgcm.encrypt(nonce, certificate, None)
    payload = nonce + ciphertext_with_tag
    if len(payload) > PAYLOAD_BYTES:
        raise ValueError("encrypted payload exceeds fixed capacity")
    padded = payload + os.urandom(PAYLOAD_BYTES - len(payload))
    return padded


def decrypt_certificate(key: bytes, padded_payload: bytes, certificate_len: int) -> bytes:
    aesgcm = AESGCM(key)
    ciphertext_len = certificate_len + TAG_LEN
    nonce = padded_payload[:NONCE_LEN]
    ciphertext_with_tag = padded_payload[NONCE_LEN:NONCE_LEN + ciphertext_len]
    return aesgcm.decrypt(nonce, ciphertext_with_tag, None)


def bytes_to_bits(data: bytes):
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits) -> bytes:
    if len(bits) % 8 != 0:
        raise ValueError("bit length must be multiple of 8")
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | int(round(b))
        out.append(byte)
    return bytes(out)