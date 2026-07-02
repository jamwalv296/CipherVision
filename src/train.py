import os
import argparse

import torch
from torch.utils.data import DataLoader

from data.dataset import CipherVisionDataset
from models.encoder import Encoder
from models.decoder import Decoder
from robustness.attacks import RobustnessLayer
from losses.losses import CipherVisionLoss


def compute_bit_accuracy(logits: torch.Tensor, payload_bits: torch.Tensor) -> float:
    probs = torch.sigmoid(logits)
    pred_bits = (probs > 0.5).float()
    return (pred_bits == payload_bits).float().mean().item()


def train(args):
    device = torch.device(args.device)

    dataset = CipherVisionDataset(args.data_dir, patch_size=args.patch_size)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers)

    encoder = Encoder(payload_bits=args.payload_bits, channels=args.channels, num_blocks=args.num_blocks).to(device)
    decoder = Decoder(payload_bits=args.payload_bits, channels=args.channels, num_blocks=args.num_blocks).to(device)
    robustness = RobustnessLayer(jpeg_quality=args.jpeg_quality).to(device)
    loss_fn = CipherVisionLoss(
        lambda_mse=args.lambda_mse,
        lambda_lpips=args.lambda_lpips,
        lambda_bce=args.lambda_bce,
    ).to(device)

    params = list(encoder.parameters()) + list(decoder.parameters())
    optimizer = torch.optim.Adam(params, lr=args.lr)

    os.makedirs(args.checkpoint_dir, exist_ok=True)

    start_epoch = 0
    best_bit_acc = 0.0
    if args.resume and os.path.exists(args.resume):
        checkpoint = torch.load(args.resume, map_location=device)
        encoder.load_state_dict(checkpoint["encoder"])
        decoder.load_state_dict(checkpoint["decoder"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        start_epoch = checkpoint["epoch"] + 1
        best_bit_acc = checkpoint.get("avg_bit_acc", 0.0)
        print(f"resumed from epoch {start_epoch}, best_bit_acc so far {best_bit_acc:.4f}")

    for epoch in range(start_epoch, args.epochs):
        encoder.train()
        decoder.train()

        epoch_loss = 0.0
        epoch_bit_acc = 0.0
        num_batches = 0

        for cover_image, payload_bits in loader:
            cover_image = cover_image.to(device)
            payload_bits = payload_bits.to(device)

            stego_image = encoder(cover_image, payload_bits)

            attacked_image = robustness(stego_image) if args.use_robustness else stego_image

            recovered_logits = decoder(attacked_image)

            total_loss, loss_breakdown = loss_fn(cover_image, stego_image, payload_bits, recovered_logits)

            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()

            bit_acc = compute_bit_accuracy(recovered_logits, payload_bits)

            epoch_loss += loss_breakdown["total_loss"]
            epoch_bit_acc += bit_acc
            num_batches += 1

            if num_batches % args.log_interval == 0:
                print(
                    f"epoch {epoch} batch {num_batches} "
                    f"loss {loss_breakdown['total_loss']:.5f} "
                    f"mse {loss_breakdown['mse_loss']:.5f} "
                    f"lpips {loss_breakdown['lpips_loss']:.5f} "
                    f"bce {loss_breakdown['bce_loss']:.5f} "
                    f"bit_acc {bit_acc:.4f}"
                )

        avg_loss = epoch_loss / num_batches
        avg_bit_acc = epoch_bit_acc / num_batches
        print(f"=== epoch {epoch} done | avg_loss {avg_loss:.5f} | avg_bit_acc {avg_bit_acc:.4f} ===")

        checkpoint_payload = {
            "epoch": epoch,
            "encoder": encoder.state_dict(),
            "decoder": decoder.state_dict(),
            "optimizer": optimizer.state_dict(),
            "avg_loss": avg_loss,
            "avg_bit_acc": avg_bit_acc,
        }

        latest_path = os.path.join(args.checkpoint_dir, "latest.pt")
        torch.save(checkpoint_payload, latest_path)

        if avg_bit_acc > best_bit_acc:
            best_bit_acc = avg_bit_acc
            best_path = os.path.join(args.checkpoint_dir, "best.pt")
            torch.save(checkpoint_payload, best_path)
            print(f"new best bit_acc {best_bit_acc:.4f}, saved: {best_path}")

        if (epoch + 1) % args.checkpoint_interval == 0 or epoch == args.epochs - 1:
            checkpoint_path = os.path.join(args.checkpoint_dir, f"checkpoint_epoch{epoch}.pt")
            torch.save(checkpoint_payload, checkpoint_path)
            print(f"saved periodic checkpoint: {checkpoint_path}")

        if avg_bit_acc >= args.target_bit_acc:
            print(f"target bit accuracy {args.target_bit_acc} reached at epoch {epoch}, stopping early")
            break


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, required=True)
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--patch_size", type=int, default=256)
    parser.add_argument("--payload_bits", type=int, default=2048)
    parser.add_argument("--channels", type=int, default=64)
    parser.add_argument("--num_blocks", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--lambda_mse", type=float, default=1.0)
    parser.add_argument("--lambda_lpips", type=float, default=0.5)
    parser.add_argument("--lambda_bce", type=float, default=1.0)
    parser.add_argument("--jpeg_quality", type=float, default=50.0)
    parser.add_argument("--use_robustness", action="store_true")
    parser.add_argument("--target_bit_acc", type=float, default=0.999)
    parser.add_argument("--num_workers", type=int, default=2)
    parser.add_argument("--log_interval", type=int, default=1)
    parser.add_argument("--checkpoint_interval", type=int, default=10)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    train(args)