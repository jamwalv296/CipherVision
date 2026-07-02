import struct
import hashlib
import time


CERT_VERSION = 1
ARTIST_ID_LEN = 16
ARTWORK_ID_LEN = 16
LICENSE_LEN = 8
HASH_LEN = 32
CERT_STRUCT_FORMAT = f"!B I {ARTIST_ID_LEN}s {ARTWORK_ID_LEN}s {LICENSE_LEN}s {HASH_LEN}s"
CERT_SIZE_BYTES = struct.calcsize(CERT_STRUCT_FORMAT)


def _pad_bytes(data: bytes, length: int) -> bytes:
    if len(data) > length:
        raise ValueError(f"field exceeds {length} bytes")
    return data + b"\x00" * (length - len(data))


def create_certificate(artist_id: str, artwork_id: str, license_code: str, image_bytes: bytes) -> bytes:
    timestamp = int(time.time())
    artwork_hash = hashlib.sha256(image_bytes).digest()
    packed = struct.pack(
        CERT_STRUCT_FORMAT,
        CERT_VERSION,
        timestamp,
        _pad_bytes(artist_id.encode("utf-8"), ARTIST_ID_LEN),
        _pad_bytes(artwork_id.encode("utf-8"), ARTWORK_ID_LEN),
        _pad_bytes(license_code.encode("utf-8"), LICENSE_LEN),
        artwork_hash,
    )
    return packed


def parse_certificate(data: bytes) -> dict:
    version, timestamp, artist_id, artwork_id, license_code, artwork_hash = struct.unpack(
        CERT_STRUCT_FORMAT, data
    )
    return {
        "version": version,
        "timestamp": timestamp,
        "artist_id": artist_id.rstrip(b"\x00").decode("utf-8"),
        "artwork_id": artwork_id.rstrip(b"\x00").decode("utf-8"),
        "license_code": license_code.rstrip(b"\x00").decode("utf-8"),
        "artwork_hash": artwork_hash.hex(),
    }