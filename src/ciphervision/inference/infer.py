import argparse
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as T

from ciphervision.models.network import CipherVisionModel
from ciphervision.crypto.crypto_utils import (
    make_certificate, encrypt_certificate, store_record,
    make_payload, verify_payload, bytes_to_bits, bits_to_bytes,
    gen_key, PAYLOAD_BYTES,
)

def load_model(ckpt_path, img_size, device):
    model = CipherVisionModel(img_size=img_size).to(device)
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model

def img_to_tensor(path, img_size, device):
    img = Image.open(path).convert("RGB")
    orig_size = img.size
    transform = T.Compose([
        T.Resize((img_size, img_size)),
        T.ToTensor(),
        T.Normalize([0.5] * 3, [0.5] * 3),
    ])
    t = transform(img).unsqueeze(0).to(device)
    return t, orig_size

def tensor_to_img(t, out_size=None):
    t = t.squeeze(0).detach().cpu()
    t = (t * 0.5 + 0.5).clamp(0, 1)
    arr = (t.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    img = Image.fromarray(arr)
    if out_size is not None:
        img = img.resize(out_size, Image.LANCZOS)
    return img

def encode_artwork(image_path, out_path, ckpt_path, artist_id, artwork_id, hmac_key, aes_key, img_size=256, db_path="cert_db.json", device="cpu"):
    model = load_model(ckpt_path, img_size, device)
    cert = make_certificate(artist_id, artwork_id)
    blob = encrypt_certificate(cert, aes_key)
    store_record(cert, blob, key_id="default", db_path=db_path)
    payload_bytes = make_payload(cert["uuid"], hmac_key)
    bits = torch.tensor(bytes_to_bits(payload_bytes), dtype=torch.float32).unsqueeze(0).to(device)

    img_t, orig_size = img_to_tensor(image_path, img_size, device)
    with torch.no_grad():
        stego, residual = model.encoder(img_t, bits)
    out_img = tensor_to_img(stego, out_size=orig_size)
    out_img.save(out_path)
    return cert["uuid"]

def decode_artwork(image_path, ckpt_path, hmac_key, aes_key, img_size=256, db_path="cert_db.json", device="cpu"):
    model = load_model(ckpt_path, img_size, device)
    img_t, _ = img_to_tensor(image_path, img_size, device)
    with torch.no_grad():
        logits = model.decoder(img_t)
        bits = torch.sigmoid(logits).squeeze(0).cpu().tolist()
    payload_bytes = bits_to_bytes(bits)
    result = verify_payload(payload_bytes, hmac_key, db_path=db_path, aes_key=aes_key)
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    e = sub.add_parser("encode")
    e.add_argument("--image", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--ckpt", required=True)
    e.add_argument("--artist_id", required=True)
    e.add_argument("--artwork_id", required=True)
    e.add_argument("--hmac_key", required=True)
    e.add_argument("--aes_key", required=True)
    e.add_argument("--img_size", type=int, default=256)
    e.add_argument("--db_path", default="cert_db.json")

    d = sub.add_parser("decode")
    d.add_argument("--image", required=True)
    d.add_argument("--ckpt", required=True)
    d.add_argument("--hmac_key", required=True)
    d.add_argument("--aes_key", required=True)
    d.add_argument("--img_size", type=int, default=256)
    d.add_argument("--db_path", default="cert_db.json")

    args = p.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if args.cmd == "encode":
        hmac_key = bytes.fromhex(args.hmac_key)
        aes_key = bytes.fromhex(args.aes_key)
        uid = encode_artwork(args.image, args.out, args.ckpt, args.artist_id, args.artwork_id, hmac_key, aes_key, args.img_size, args.db_path, device)
        print(f"encoded uuid: {uid}")

    elif args.cmd == "decode":
        hmac_key = bytes.fromhex(args.hmac_key)
        aes_key = bytes.fromhex(args.aes_key)
        result = decode_artwork(args.image, args.ckpt, hmac_key, aes_key, args.img_size, args.db_path, device)
        print(result)
