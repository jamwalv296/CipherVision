import os
import time
import argparse
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast, GradScaler

from ciphervision.models.network import CipherVisionModel
from ciphervision.data.div2k_dataset import DIV2KDataset

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument("--train_dir", type=str, required=True)
    p.add_argument("--val_dir", type=str, required=True)
    p.add_argument("--ckpt_dir", type=str, required=True)
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--img_size", type=int, default=256)
    p.add_argument("--resume", type=str, default="")
    return p.parse_args()

def bit_accuracy(logits, target):
    pred = (torch.sigmoid(logits) > 0.5).float()
    return (pred == target).float().mean().item()

def main():
    args = get_args()
    os.makedirs(args.ckpt_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_ds = DIV2KDataset(args.train_dir, args.img_size, train=True)
    val_ds = DIV2KDataset(args.val_dir, args.img_size, train=False)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=4, pin_memory=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=2, pin_memory=True)

    model = CipherVisionModel(img_size=args.img_size).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    scaler = GradScaler()
    mse = nn.MSELoss()
    bce = nn.BCEWithLogitsLoss()

    start_epoch = 0
    best_val_acc = 0.0

    if args.resume and os.path.exists(args.resume):
        ckpt = torch.load(args.resume, map_location=device)
        model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["opt"])
        start_epoch = ckpt["epoch"] + 1
        best_val_acc = ckpt.get("best_val_acc", 0.0)
        print(f"resumed from epoch {start_epoch}")

    for epoch in range(start_epoch, args.epochs):
        model.train()
        img_weight = min(2.0, 0.5 + epoch * 0.02)
        bit_weight = 1.0
        t0 = time.time()
        running_img_loss = 0.0
        running_bit_loss = 0.0
        running_acc = 0.0
        n_batches = 0

        for image, payload in train_loader:
            image = image.to(device, non_blocking=True)
            payload = payload.to(device, non_blocking=True)

            opt.zero_grad()
            with autocast():
                stego, residual, recovered = model(image, payload)
                img_loss = mse(stego, image)
                bit_loss = bce(recovered, payload)
                loss = img_weight * img_loss + bit_weight * bit_loss

            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()

            running_img_loss += img_loss.item()
            running_bit_loss += bit_loss.item()
            running_acc += bit_accuracy(recovered, payload)
            n_batches += 1

        train_img_loss = running_img_loss / n_batches
        train_bit_loss = running_bit_loss / n_batches
        train_acc = running_acc / n_batches

        model.eval()
        val_img_loss = 0.0
        val_bit_loss = 0.0
        val_acc = 0.0
        vn = 0
        with torch.no_grad():
            for image, payload in val_loader:
                image = image.to(device)
                payload = payload.to(device)
                stego, residual, recovered = model(image, payload)
                val_img_loss += mse(stego, image).item()
                val_bit_loss += bce(recovered, payload).item()
                val_acc += bit_accuracy(recovered, payload)
                vn += 1
        val_img_loss /= vn
        val_bit_loss /= vn
        val_acc /= vn

        dt = time.time() - t0
        print(f"epoch {epoch} | train_img {train_img_loss:.5f} train_bit {train_bit_loss:.5f} train_acc {train_acc:.4f} | val_img {val_img_loss:.5f} val_bit {val_bit_loss:.5f} val_acc {val_acc:.4f} | {dt:.1f}s")

        ckpt = {
            "model": model.state_dict(),
            "opt": opt.state_dict(),
            "epoch": epoch,
            "best_val_acc": best_val_acc,
            "img_size": args.img_size,
        }
        torch.save(ckpt, os.path.join(args.ckpt_dir, "last.pt"))

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            ckpt["best_val_acc"] = best_val_acc
            torch.save(ckpt, os.path.join(args.ckpt_dir, "best.pt"))

if __name__ == "__main__":
    main()
