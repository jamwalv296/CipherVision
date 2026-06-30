# CipherVision

Invisible AI watermarking for digital artwork. Embeds an authenticated 256-bit
certificate ID inside an image via learned steganography; full certificate is
stored encrypted server-side and resolved via UUID at decode time.

## Structure

```
ciphervision_project/
├── src/ciphervision/
│   ├── models/network.py        # Encoder, Decoder, NoiseLayer, CipherVisionModel
│   ├── data/div2k_dataset.py    # DIV2K dataset loader
│   ├── crypto/crypto_utils.py   # cert encryption, HMAC payload, DB
│   ├── training/train.py        # training loop (Colab-ready)
│   └── inference/infer.py       # encode/decode CLI
├── scripts/generate_keys.py     # generate HMAC/AES keys
├── configs/train_config.yaml
├── notebooks/COLAB_CELLS.txt    # Colab cell-by-cell setup
├── checkpoints/                 # .pt files (gitignored)
├── data/DIV2K/train/             # 800 images (gitignored)
├── data/DIV2K/valid/             # 100 images (gitignored)
├── secrets/                     # keys, cert_db.json (gitignored)
└── tests/
```

## Setup

```bash
pip install -e .
python scripts/generate_keys.py > secrets/keys.env
```

## Train (Colab)

See `notebooks/COLAB_CELLS.txt`. Checkpoints write directly to Drive.

## Encode / Decode

```bash
python -m ciphervision.inference.infer encode \
  --image art.png --out art_protected.png \
  --ckpt checkpoints/best.pt \
  --artist_id artist1 --artwork_id art1 \
  --hmac_key <hex> --aes_key <hex> \
  --db_path secrets/cert_db.json

python -m ciphervision.inference.infer decode \
  --image art_protected.png \
  --ckpt checkpoints/best.pt \
  --hmac_key <hex> --aes_key <hex> \
  --db_path secrets/cert_db.json
```
