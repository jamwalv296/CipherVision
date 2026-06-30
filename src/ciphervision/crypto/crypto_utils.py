import os
import json
import uuid
import time
import hmac
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PAYLOAD_BITS = 256
PAYLOAD_BYTES = PAYLOAD_BITS // 8

def gen_key():
    return AESGCM.generate_key(bit_length=256)

def make_certificate(artist_id, artwork_id, extra=None):
    return {
        "artist_id": artist_id,
        "artwork_id": artwork_id,
        "uuid": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "extra": extra or {},
    }

def encrypt_certificate(cert, key):
    plaintext = json.dumps(cert, sort_keys=True).encode()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ct

def decrypt_certificate(blob, key):
    nonce, ct = blob[:12], blob[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ct, None)
    return json.loads(plaintext.decode())

def store_record(cert, encrypted_blob, key_id, db_path="cert_db.json"):
    db = {}
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            db = json.load(f)
    db[cert["uuid"]] = {
        "encrypted_certificate": encrypted_blob.hex(),
        "key_id": key_id,
    }
    with open(db_path, "w") as f:
        json.dump(db, f, indent=2)
    return cert["uuid"]

def make_payload(cert_uuid, hmac_key):
    uuid_bytes = uuid.UUID(cert_uuid).bytes
    tag = hmac.new(hmac_key, uuid_bytes, hashlib.sha256).digest()[:16]
    payload = uuid_bytes + tag
    assert len(payload) == PAYLOAD_BYTES
    return payload

def verify_payload(payload_bytes, hmac_key, db_path="cert_db.json", aes_key=None):
    uuid_bytes = payload_bytes[:16]
    tag = payload_bytes[16:32]
    expected_tag = hmac.new(hmac_key, uuid_bytes, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(tag, expected_tag):
        return None
    cert_uuid = str(uuid.UUID(bytes=uuid_bytes))
    with open(db_path, "r") as f:
        db = json.load(f)
    record = db.get(cert_uuid)
    if record is None:
        return None
    if aes_key is None:
        return {"uuid": cert_uuid, "verified": True}
    blob = bytes.fromhex(record["encrypted_certificate"])
    return decrypt_certificate(blob, aes_key)

def bytes_to_bits(b):
    bits = []
    for byte in b:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits

def bits_to_bytes(bits):
    bits = [1 if b > 0.5 else 0 for b in bits]
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        out.append(byte)
    return bytes(out)
