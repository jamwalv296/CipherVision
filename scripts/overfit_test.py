import os
import sys
import shutil
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")))

import torch
from torch.utils.data import DataLoader

from data.dataset import CipherVisionDataset
from models.encoder import Encoder
from models.decoder import Decoder
from losses.losses import CipherVisionLoss


def prepare_overfit_set(source_dir: str, target_dir: str, num_images: int = 20):
    os.makedirs(target_dir, exist_ok=True)
    existing = [f for f in os.listdir(target_dir) if os.path.splitext(f)[1].lower() in {".png", ".jpg", ".jpeg"}]
    if len(existing) >= num_images:
        print(f"overfit set already prepared with {len(existing)} images")
        return

    source_files = sorted([
        f for f in os.listdir(source_dir)
        if os.path.splitext(f)[1].lower() in {".png", ".jpg", ".jpeg"}
    ])[:num_images]

    for f in source_files:
        shutil.copy(os.path.join(source_dir, f), os.path.join(target_dir, f))

    print(f"copied {len(source_files)} images to {target_dir}")


def compute_bit_accuracy(logits: torch.Tensor, payload_bits: torch.Tensor) -> float:
    probs = torch.sigmoid(logits)
    pred_bits = (probs > 0.5).float()
    return (pred_bits == payload_bits).float().mean().item()


def run_overfit_test(args):
    device = torch.device(args.device)

    prepare_overfit_set(args.source_dir, args.overfit_dir, args.num_images)

    dataset = CipherVisionDataset(args.overfit_dir, patch_size=args.patch_size)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)

    encoder = Encoder(payload_bits=args.payload_bits, channels=args.channels, num_blocks=args.num_blocks).to(device)
    decoder = Decoder(payload_bits=args.payload_bits, channels=args.channels, num_blocks=args.num_blocks).to(device)
    loss_fn = CipherVisionLoss(
        lambda_mse=args.lambda_mse,
        lambda_lpips=args.lambda_lpips,
        lambda_bce=args.lambda_bce,
    ).to(device)

    params = list(encoder.parameters()) + list(decoder.parameters())
    optimizer = torch.optim.Adam(params, lr=args.lr)

    best_bit_acc = 0.0

    for epoch in range(args.epochs):
        encoder.train()
        decoder.train()

        epoch_loss = 0.0
        epoch_bit_acc = 0.0
        num_batches = 0

        for cover_image, payload_bits in loader:
            cover_image = cover_image.to(device)
            payload_bits = payload_bits.to(device)

            stego_image = encoder(cover_image, payload_bits)
            recovered_logits = decoder(stego_image)

            total_loss, loss_breakdown = loss_fn(cover_image, stego_image, payload_bits, recovered_logits)

            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()

            bit_acc = compute_bit_accuracy(recovered_logits, payload_bits)

            epoch_loss += loss_breakdown["total_loss"]
            epoch_bit_acc += bit_acc
            num_batches += 1

        avg_loss = epoch_loss / num_batches
        avg_bit_acc = epoch_bit_acc / num_batches
        best_bit_acc = max(best_bit_acc, avg_bit_acc)

        if epoch % args.log_interval == 0 or epoch == args.epochs - 1:
            print(f"epoch {epoch} | loss {avg_loss:.5f} | bit_acc {avg_bit_acc:.4f} | best {best_bit_acc:.4f}")

        if avg_bit_acc >= args.target_bit_acc:
            print(f"PASSED: target bit accuracy {args.target_bit_acc} reached at epoch {epoch}")
            return True

    print(f"FAILED: did not reach target bit accuracy {args.target_bit_acc}, best was {best_bit_acc:.4f}")
    return False


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=str, default="data/DIV2K_train_HR")
    parser.add_argument("--overfit_dir", type=str, default="data/overfit_20")
    parser.add_argument("--num_images", type=int, default=20)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--patch_size", type=int, default=256)
    parser.add_argument("--payload_bits", type=int, default=2048)
    parser.add_argument("--channels", type=int, default=64)
    parser.add_argument("--num_blocks", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--lambda_mse", type=float, default=1.0)
    parser.add_argument("--lambda_lpips", type=float, default=0.5)
    parser.add_argument("--lambda_bce", type=float, default=1.0)
    parser.add_argument("--target_bit_acc", type=float, default=0.95)
    parser.add_argument("--log_interval", type=int, default=10)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    passed = run_overfit_test(args)
    sys.exit(0 if passed else 1)