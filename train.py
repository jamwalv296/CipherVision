import os
import torch
import torch.optim as optim
from torch.utils.data import DataLoader

from src.dataset import DIV2KPayloadDataset
from src.models import CipherVision
from src.robustness import RobustnessLayer
from src.loss import CipherVisionLoss

def train(data_dir="data", epochs=30, batch_size=16, lr=1e-4, save_path="models/ciphervision_final.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training initialized on device: {device}")
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    train_dataset = DIV2KPayloadDataset(img_dir=data_dir, payload_len=64)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    model = CipherVision(payload_len=64).to(device)
    robustness = RobustnessLayer().to(device)
    criterion = CipherVisionLoss(mse_weight=1.0, lpips_weight=1.0, bce_weight=10.0, device=device).to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    print("Starting full-scale training pipeline with robustness attacks...")
    
    for epoch in range(epochs):
        model.train()
        robustness.train()
        
        epoch_loss = 0.0
        epoch_img_loss = 0.0
        epoch_bce_loss = 0.0
        correct_bits = 0
        total_bits = 0
        
        for imgs, payloads in train_loader:
            imgs, payloads = imgs.to(device), payloads.to(device)
            optimizer.zero_grad()
            
            stego_imgs = model.encoder(imgs, payloads)
            attacked_imgs = robustness(stego_imgs)
            recovered_payloads = model.decoder(attacked_imgs)
            
            loss, img_loss, bce_loss, _, _ = criterion(imgs, stego_imgs, payloads, recovered_payloads)
            
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            epoch_img_loss += img_loss.item()
            epoch_bce_loss += bce_loss.item()
            
            preds = (recovered_payloads > 0.5).float()
            correct_bits += (preds == payloads).sum().item()
            total_bits += payloads.numel()
            
        avg_loss = epoch_loss / len(train_loader)
        avg_img_loss = epoch_img_loss / len(train_loader)
        avg_bce_loss = epoch_bce_loss / len(train_loader)
        bit_acc = (correct_bits / total_bits) * 100
        
        print(f"Epoch {epoch+1}/{epochs} | Total Loss: {avg_loss:.4f} (Img: {avg_img_loss:.4f}, Payload: {avg_bce_loss:.4f}) | Bit Acc: {bit_acc:.2f}%")
        
    torch.save(model.state_dict(), save_path)
    print(f"Training complete. Weights securely saved to {save_path}")

if __name__ == "__main__":
    train()